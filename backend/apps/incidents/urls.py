from django.urls import path

from .views import (
    IncidentListCreateView,
    IncidentDetailView,
    IncidentNotesListView,
    IncidentNoteCreateView,
)

app_name = 'incidents'

urlpatterns = [
    path('', IncidentListCreateView.as_view(), name='list-create'),
    path('<int:pk>/', IncidentDetailView.as_view(), name='detail'),
    path('<int:incident_id>/notes/', IncidentNotesListView.as_view(), name='notes-list'),
    path('<int:incident_id>/notes/create/', IncidentNoteCreateView.as_view(), name='notes-create'),
]
