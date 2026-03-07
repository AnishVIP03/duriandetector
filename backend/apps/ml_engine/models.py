from django.db import models


class MLModelConfig(models.Model):
    """Configuration for the ML model used in an environment."""

    class ModelType(models.TextChoices):
        RANDOM_FOREST = 'random_forest', 'Random Forest'
        SVM = 'svm', 'SVM'
        ISOLATION_FOREST = 'isolation_forest', 'Isolation Forest'
        NEURAL_NET = 'neural_net', 'Neural Network'

    class Sensitivity(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    environment = models.OneToOneField(
        'environments.Environment',
        on_delete=models.CASCADE,
        related_name='ml_config',
    )
    model_type = models.CharField(
        max_length=20,
        choices=ModelType.choices,
        default=ModelType.RANDOM_FOREST,
    )
    sensitivity = models.CharField(
        max_length=10,
        choices=Sensitivity.choices,
        default=Sensitivity.MEDIUM,
    )
    detection_threshold = models.FloatField(default=0.5)
    alert_threshold = models.JSONField(default=dict, blank=True)
    trained_at = models.DateTimeField(null=True, blank=True)
    model_file_path = models.CharField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'ML Model Config'
        verbose_name_plural = 'ML Model Configs'

    def __str__(self):
        return f"{self.model_type} for {self.environment} (active={self.is_active})"


class MLModelMetrics(models.Model):
    """Performance metrics for an ML model evaluation."""

    config = models.ForeignKey(
        MLModelConfig,
        on_delete=models.CASCADE,
        related_name='metrics',
    )
    accuracy = models.FloatField()
    precision = models.FloatField()
    recall = models.FloatField()
    f1_score = models.FloatField()
    training_samples = models.IntegerField()
    evaluated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-evaluated_at']
        verbose_name = 'ML Model Metrics'
        verbose_name_plural = 'ML Model Metrics'

    def __str__(self):
        return f"Metrics for {self.config} (F1={self.f1_score})"
