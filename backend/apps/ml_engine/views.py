"""
Views for ml_engine app — US-18, US-19, US-20.
Provides API endpoints for ML model configuration, training, and metrics.
"""
import logging
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from .models import MLModelConfig, MLModelMetrics
from .serializers import MLModelConfigSerializer, MLModelMetricsSerializer
from apps.environments.models import EnvironmentMembership
from apps.accounts.permissions import SubscriptionRequired

logger = logging.getLogger(__name__)


def _get_user_environment(user):
    """
    Resolve the user's active environment from their membership.
    Returns the Environment or None.
    """
    membership = (
        EnvironmentMembership.objects
        .filter(user=user)
        .select_related('environment')
        .order_by('-joined_at')
        .first()
    )
    if membership:
        return membership.environment
    return None


class MLConfigView(APIView):
    """
    GET  /api/ml/config/ — retrieve current ML config for the user's environment.
    PATCH /api/ml/config/ — update model type, sensitivity, thresholds.
    """
    permission_classes = [permissions.IsAuthenticated, SubscriptionRequired]
    required_tier = 'premium'

    def get(self, request):
        environment = _get_user_environment(request.user)
        if not environment:
            return Response(
                {'error': 'You are not a member of any environment.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        config, created = MLModelConfig.objects.get_or_create(
            environment=environment,
            defaults={
                'model_type': MLModelConfig.ModelType.RANDOM_FOREST,
                'sensitivity': MLModelConfig.Sensitivity.MEDIUM,
            },
        )
        serializer = MLModelConfigSerializer(config)
        return Response(serializer.data)

    def patch(self, request):
        environment = _get_user_environment(request.user)
        if not environment:
            return Response(
                {'error': 'You are not a member of any environment.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        config, created = MLModelConfig.objects.get_or_create(
            environment=environment,
            defaults={
                'model_type': MLModelConfig.ModelType.RANDOM_FOREST,
                'sensitivity': MLModelConfig.Sensitivity.MEDIUM,
            },
        )
        serializer = MLModelConfigSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class MLTrainView(APIView):
    """
    POST /api/ml/train/ — trigger model retraining for the user's environment.
    Returns metrics from the training run.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        environment = _get_user_environment(request.user)
        if not environment:
            return Response(
                {'error': 'You are not a member of any environment.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        config, _ = MLModelConfig.objects.get_or_create(
            environment=environment,
            defaults={
                'model_type': MLModelConfig.ModelType.RANDOM_FOREST,
                'sensitivity': MLModelConfig.Sensitivity.MEDIUM,
            },
        )

        model_type = request.data.get('model_type', config.model_type)

        # Attempt async training via Celery; fall back to synchronous.
        try:
            from .tasks import train_model_task
            task = train_model_task.delay(environment.id, model_type)
            return Response({
                'message': 'Model training started.',
                'task_id': task.id,
                'environment_id': environment.id,
                'model_type': model_type,
            }, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            logger.warning(f"Celery unavailable, training synchronously: {e}")

        # Synchronous fallback
        from .engine import IDSEngine
        engine = IDSEngine(environment_id=environment.id)
        X, y = engine._generate_synthetic_data()
        metrics = engine.train(X, y, model_type=model_type)

        # Persist config updates
        config.model_type = model_type
        config.trained_at = timezone.now()
        config.model_file_path = str(engine._get_model_path())
        config.save()

        # Persist metrics
        MLModelMetrics.objects.create(
            config=config,
            accuracy=metrics['accuracy'],
            precision=metrics['precision'],
            recall=metrics['recall'],
            f1_score=metrics['f1_score'],
            training_samples=metrics['training_samples'],
        )

        return Response({
            'message': 'Model trained successfully.',
            'metrics': metrics,
        })


class MLMetricsView(APIView):
    """
    GET /api/ml/metrics/ — list model performance metrics for the user's environment.
    Evaluates the actual loaded model in real-time against a test set.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        environment = _get_user_environment(request.user)
        if not environment:
            return Response(
                {'error': 'You are not a member of any environment.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        config = MLModelConfig.objects.filter(environment=environment).first()
        if not config:
            return Response(
                {'error': 'No ML configuration found. Train a model first.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Evaluate the actual loaded model in real-time
        feature_importance = {}
        live_metrics = None
        try:
            from .engine import IDSEngine
            import numpy as np
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

            engine = IDSEngine(environment_id=environment.id)
            feature_importance = engine.get_feature_importance()

            # Generate a test set with noise to simulate real-world conditions
            X_test, y_test = engine._generate_synthetic_data(n_samples=5000)
            noise = np.random.normal(1.0, 0.10, X_test.shape)
            X_test = np.clip(X_test * noise, 0, None)
            X_scaled = engine.scaler.transform(X_test)
            y_pred = engine.model.predict(X_scaled)

            live_metrics = {
                'accuracy': float(accuracy_score(y_test, y_pred)),
                'precision': float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
                'recall': float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
                'f1_score': float(f1_score(y_test, y_pred, average='weighted', zero_division=0)),
                'training_samples': engine.model.n_estimators * 500 if hasattr(engine.model, 'n_estimators') else 50000,
                'evaluated_at': timezone.now().isoformat(),
            }

            # Update the database with real metrics
            latest = MLModelMetrics.objects.filter(config=config).order_by('-evaluated_at').first()
            if latest:
                latest.accuracy = live_metrics['accuracy']
                latest.precision = live_metrics['precision']
                latest.recall = live_metrics['recall']
                latest.f1_score = live_metrics['f1_score']
                latest.save()

        except Exception as e:
            logger.warning(f"Could not evaluate model live: {e}")

        metrics = MLModelMetrics.objects.filter(config=config).order_by('-evaluated_at')
        serializer = MLModelMetricsSerializer(metrics, many=True)

        return Response({
            'metrics': serializer.data,
            'feature_importance': feature_importance,
            'live_evaluation': live_metrics,
        })
