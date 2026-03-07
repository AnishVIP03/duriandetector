from django.contrib import admin
from .models import CaptureSession, NetworkFeature


@admin.register(CaptureSession)
class CaptureSessionAdmin(admin.ModelAdmin):
    list_display = [
        'environment', 'interface', 'status', 'packets_captured',
        'alerts_generated', 'started_by', 'started_at', 'stopped_at',
    ]
    list_filter = ['status']
    search_fields = ['interface']


@admin.register(NetworkFeature)
class NetworkFeatureAdmin(admin.ModelAdmin):
    list_display = [
        'session', 'src_ip', 'dst_ip', 'src_port', 'dst_port',
        'protocol', 'packet_length', 'ttl', 'timestamp',
    ]
    search_fields = ['src_ip', 'dst_ip']
