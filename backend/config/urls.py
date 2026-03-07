"""
Root URL configuration for IDS project.
All API endpoints are namespaced under /api/.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/auth/', include('apps.accounts.urls')),
    path('api/environments/', include('apps.environments.urls')),
    path('api/subscriptions/', include('apps.subscriptions.urls')),
    path('api/alerts/', include('apps.alerts.urls')),
    path('api/incidents/', include('apps.incidents.urls')),
    path('api/threats/', include('apps.threats.urls')),
    path('api/ml/', include('apps.ml_engine.urls')),
    path('api/capture/', include('apps.network_capture.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/admin-panel/', include('apps.audit.urls')),
    path('api/chatbot/', include('apps.chatbot.urls')),
    path('api/mitre/', include('apps.mitre.urls')),
    path('api/attack-chains/', include('apps.attack_chains.urls')),
    path('api/demo/', include('apps.demo.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
