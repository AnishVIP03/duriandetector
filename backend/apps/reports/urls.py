from django.urls import path

from .views import (
    ReportListView,
    GenerateReportView,
    ReportDetailView,
    ReportExportView,
)

app_name = 'reports'

urlpatterns = [
    path('', ReportListView.as_view(), name='list'),
    path('generate/', GenerateReportView.as_view(), name='generate'),
    path('<int:pk>/', ReportDetailView.as_view(), name='detail'),
    path('<int:pk>/export/', ReportExportView.as_view(), name='export'),
]
