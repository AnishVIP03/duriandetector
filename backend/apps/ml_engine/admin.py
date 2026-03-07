from django.contrib import admin
from .models import MLModelConfig, MLModelMetrics


@admin.register(MLModelConfig)
class MLModelConfigAdmin(admin.ModelAdmin):
    list_display = [
        'environment', 'model_type', 'sensitivity',
        'detection_threshold', 'trained_at', 'is_active',
    ]
    list_filter = ['model_type', 'sensitivity', 'is_active']


@admin.register(MLModelMetrics)
class MLModelMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'config', 'accuracy', 'precision', 'recall',
        'f1_score', 'training_samples', 'evaluated_at',
    ]
