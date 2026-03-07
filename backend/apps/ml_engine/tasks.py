"""
Celery tasks for ml_engine app.
Provides async model training so the API can return immediately.
"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def train_model_task(environment_id, model_type='random_forest'):
    """Async task to train ML model for an environment."""
    from .engine import IDSEngine
    from .models import MLModelConfig, MLModelMetrics

    logger.info(f"Training model for env {environment_id}, type={model_type}")

    engine = IDSEngine(environment_id=environment_id)
    engine._train_default()  # For now, retrain with synthetic data

    # Update config
    try:
        config = MLModelConfig.objects.get(environment_id=environment_id)
        config.trained_at = timezone.now()
        config.model_file_path = str(engine._get_model_path())
        config.save()

        # Evaluate on a held-out test set and save metrics
        import numpy as np
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score, f1_score,
        )

        X, y = engine._generate_synthetic_data()
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        X_test_scaled = engine.scaler.transform(X_test)
        y_pred = engine.model.predict(X_test_scaled)

        MLModelMetrics.objects.create(
            config=config,
            accuracy=accuracy_score(y_test, y_pred),
            precision=precision_score(
                y_test, y_pred, average='weighted', zero_division=0
            ),
            recall=recall_score(
                y_test, y_pred, average='weighted', zero_division=0
            ),
            f1_score=f1_score(
                y_test, y_pred, average='weighted', zero_division=0
            ),
            training_samples=len(X_train),
            evaluated_at=timezone.now(),
        )
    except MLModelConfig.DoesNotExist:
        logger.warning(
            f"MLModelConfig for env {environment_id} not found; "
            "skipping metrics persistence."
        )

    return {'status': 'completed', 'environment_id': environment_id}
