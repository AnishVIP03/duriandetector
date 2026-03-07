"""
Serializers for reports app — US-22, US-23.
"""
from rest_framework import serializers
from .models import Report


class ReportListSerializer(serializers.ModelSerializer):
    """Compact report serializer for list views — US-22."""
    created_by = serializers.CharField(source='created_by.email', read_only=True)
    has_pdf = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            'id', 'environment', 'created_by', 'title', 'report_type',
            'date_from', 'date_to', 'created_at', 'has_pdf',
        ]

    def get_has_pdf(self, obj):
        return bool(obj.pdf_file)


class ReportDetailSerializer(serializers.ModelSerializer):
    """Full report serializer including content JSON — US-22."""
    created_by = serializers.CharField(source='created_by.email', read_only=True)
    has_pdf = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            'id', 'environment', 'created_by', 'title', 'report_type',
            'date_from', 'date_to', 'content', 'pdf_file', 'created_at',
            'has_pdf',
        ]

    def get_has_pdf(self, obj):
        return bool(obj.pdf_file)


class GenerateReportSerializer(serializers.Serializer):
    """Serializer for report generation request — US-22."""
    title = serializers.CharField(required=True, max_length=255)
    report_type = serializers.ChoiceField(
        choices=['summary', 'detailed', 'incident', 'threat'],
    )
    date_from = serializers.DateTimeField()
    date_to = serializers.DateTimeField()
