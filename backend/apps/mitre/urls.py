from django.urls import path
from . import views

app_name = 'mitre'

urlpatterns = [
    path('heatmap/', views.MitreHeatmapView.as_view(), name='heatmap'),
    path('techniques/<str:technique_id>/', views.MitreTechniqueDetailView.as_view(), name='technique-detail'),
]
