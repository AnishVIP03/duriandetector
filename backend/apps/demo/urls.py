from django.urls import path
from . import views

app_name = 'demo'

urlpatterns = [
    path('start/', views.DemoStartView.as_view(), name='start'),
    path('status/', views.DemoStatusView.as_view(), name='status'),
    path('clear/', views.DemoClearView.as_view(), name='clear'),
]
