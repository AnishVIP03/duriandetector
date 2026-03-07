"""
URL routes for network_capture app.
Base path: /api/capture/
"""
from django.urls import path
from . import views

app_name = 'network_capture'

urlpatterns = [
    path('start/', views.StartCaptureView.as_view(), name='start'),
    path('stop/', views.StopCaptureView.as_view(), name='stop'),
    path('status/', views.CaptureStatusView.as_view(), name='status'),
]
