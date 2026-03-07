from django.contrib import admin
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'report_type', 'environment', 'created_by',
        'date_from', 'date_to', 'created_at',
    ]
    list_filter = ['report_type']
    search_fields = ['title']
