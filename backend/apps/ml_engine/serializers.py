"""
Serializers for ml_engine app — US-18, US-19, US-20.
"""
from rest_framework import serializers
from .models import MLModelConfig, MLModelMetrics


class MLModelConfigSerializer(serializers.ModelSerializer):
    """Serializer for viewing / updating ML model configuration."""

    class Meta:
        model = MLModelConfig
        fields = [
            'id', 'environment', 'model_type', 'sensitivity',
            'detection_threshold', 'alert_threshold', 'trained_at',
            'model_file_path', 'is_active',
        ]
        read_only_fields = ['id', 'trained_at', 'model_file_path']


class MLModelMetricsSerializer(serializers.ModelSerializer):
    """Serializer for ML model performance metrics."""

    class Meta:
        model = MLModelMetrics
        fields = [
            'id', 'config', 'accuracy', 'precision', 'recall',
            'f1_score', 'training_samples', 'evaluated_at',
        ]
        read_only_fields = ['id']
