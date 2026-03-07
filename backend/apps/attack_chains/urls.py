from django.urls import path
from . import views

app_name = 'attack_chains'

urlpatterns = [
    path('', views.AttackChainListView.as_view(), name='list'),
    path('<int:pk>/', views.AttackChainDetailView.as_view(), name='detail'),
    path('risk-score/', views.DynamicRiskScoreView.as_view(), name='risk-score'),
]
