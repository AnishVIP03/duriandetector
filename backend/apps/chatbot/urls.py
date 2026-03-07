from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('sessions/', views.ChatSessionListView.as_view(), name='sessions'),
    path('sessions/<int:pk>/', views.ChatSessionDetailView.as_view(), name='session-detail'),
    path('sessions/<int:pk>/delete/', views.DeleteChatSessionView.as_view(), name='session-delete'),
    path('send/', views.ChatSendMessageView.as_view(), name='send'),
]
