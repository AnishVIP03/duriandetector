"""
URL routes for ml_engine app — US-18, US-19, US-20.
Base path: /api/ml/
"""
from django.urls import path
from . import views

app_name = 'ml_engine'

urlpatterns = [
    path('config/', views.MLConfigView.as_view(), name='config'),
    path('train/', views.MLTrainView.as_view(), name='train'),
    path('metrics/', views.MLMetricsView.as_view(), name='metrics'),
]
