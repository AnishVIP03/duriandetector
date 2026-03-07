from django.urls import path

from .views import ThreatListView, ThreatCorrelationView

app_name = 'threats'

urlpatterns = [
    path('', ThreatListView.as_view(), name='list'),
    path('<str:ip>/correlate/', ThreatCorrelationView.as_view(), name='correlate'),
]
