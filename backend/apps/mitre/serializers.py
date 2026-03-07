from rest_framework import serializers
from .models import MitreTactic, MitreTechnique


class MitreTechniqueSerializer(serializers.ModelSerializer):
    alert_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = MitreTechnique
        fields = ['id', 'technique_id', 'name', 'description', 'tactic', 'alert_count']


class MitreTacticSerializer(serializers.ModelSerializer):
    techniques = MitreTechniqueSerializer(many=True, read_only=True)

    class Meta:
        model = MitreTactic
        fields = ['id', 'tactic_id', 'name', 'description', 'techniques']
