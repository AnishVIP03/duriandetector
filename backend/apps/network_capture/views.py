"""
Views for network_capture app — US-21, packet capture management.
"""
import random
import threading
import time
import logging

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import CaptureSession
from .serializers import CaptureSessionSerializer, StartCaptureSerializer
from apps.environments.models import EnvironmentMembership
from apps.accounts.permissions import SubscriptionRequired

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory registry of running simulation threads (keyed by user id)
# ---------------------------------------------------------------------------
_simulation_threads = {}
_simulation_lock = threading.Lock()


class StartCaptureView(APIView):
    """Start a new packet capture session."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = StartCaptureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get user's environment
        membership = EnvironmentMembership.objects.filter(
            user=request.user
        ).select_related('environment').first()

        if not membership:
            return Response(
                {'error': 'You must belong to an environment to start capture.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        env = membership.environment

        # Check for existing running session
        running = CaptureSession.objects.filter(
            environment=env, status='running'
        ).first()
        if running:
            return Response(
                {'error': 'A capture session is already running.',
                 'session': CaptureSessionSerializer(running).data},
                status=status.HTTP_409_CONFLICT,
            )

        # Create capture session
        session = CaptureSession.objects.create(
            environment=env,
            interface=serializer.validated_data.get('interface') or env.network_interface,
            status='running',
            started_by=request.user,
        )

        # Launch Celery task
        try:
            from .tasks import capture_packets_task
            capture_packets_task.delay(
                session_id=session.id,
                environment_id=env.id,
                interface=session.interface,
                packet_count=serializer.validated_data.get('packet_count', 0),
                duration=serializer.validated_data.get('duration', 300),
            )
        except Exception as e:
            # If Celery is not running, mark session as error
            session.status = 'error'
            session.save(update_fields=['status'])
            return Response(
                {'error': f'Failed to start capture task: {str(e)}. Is Celery running?'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                'message': 'Capture session started.',
                'session': CaptureSessionSerializer(session).data,
            },
            status=status.HTTP_201_CREATED,
        )


class StopCaptureView(APIView):
    """Stop a running capture session."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        membership = EnvironmentMembership.objects.filter(
            user=request.user
        ).select_related('environment').first()

        if not membership:
            return Response(
                {'error': 'No environment found.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session = CaptureSession.objects.filter(
            environment=membership.environment, status='running'
        ).first()

        if not session:
            return Response(
                {'error': 'No running capture session found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        session.status = 'stopped'
        session.stopped_at = timezone.now()
        session.save(update_fields=['status', 'stopped_at'])

        return Response({
            'message': 'Capture session stopped.',
            'session': CaptureSessionSerializer(session).data,
        })


class CaptureStatusView(APIView):
    """Get the current capture session status — US-21."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        membership = EnvironmentMembership.objects.filter(
            user=request.user
        ).select_related('environment').first()

        if not membership:
            return Response(
                {'error': 'No environment found.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Current running session
        current = CaptureSession.objects.filter(
            environment=membership.environment, status='running'
        ).order_by('-started_at').first()

        # Get latest sessions
        sessions = CaptureSession.objects.filter(
            environment=membership.environment
        ).order_by('-started_at')[:10]

        return Response({
            'current_session': CaptureSessionSerializer(current).data if current else None,
            'is_capturing': current is not None,
            'recent_sessions': CaptureSessionSerializer(sessions, many=True).data,
        })


# ---------------------------------------------------------------------------
# Packet simulation data (mirrors demo app style)
# ---------------------------------------------------------------------------

_SIM_SOURCE_IPS = [
    '185.220.101.42', '103.253.41.98', '45.155.205.233',
    '91.240.118.172', '198.51.100.23', '203.0.113.45',
    '177.54.150.100', '10.0.1.55', '192.168.1.10',
    '172.16.0.22', '59.24.3.174', '78.128.113.18',
]

_SIM_DST_IPS = [
    '10.0.1.10', '10.0.1.20', '10.0.1.30', '10.0.2.10',
    '192.168.1.100', '192.168.1.200', '172.16.0.5',
]

_SIM_PROTOCOLS = ['TCP', 'UDP', 'ICMP', 'HTTP', 'DNS', 'SSH']

_SIM_FLAGS = ['SYN', 'SYN-ACK', 'ACK', 'FIN', 'RST', 'PSH-ACK', 'URG', '']


def _generate_simulated_packet():
    """Generate a single realistic-looking simulated packet dict."""
    protocol = random.choice(_SIM_PROTOCOLS)
    src_port = random.randint(1024, 65535) if protocol != 'ICMP' else None
    dst_port_map = {
        'HTTP': [80, 443, 8080],
        'DNS': [53],
        'SSH': [22],
        'TCP': [80, 443, 22, 3306, 5432, 8080, 8443],
        'UDP': [53, 123, 161, 5060],
        'ICMP': [None],
    }
    dst_port = random.choice(dst_port_map.get(protocol, [80]))

    return {
        'src_ip': random.choice(_SIM_SOURCE_IPS),
        'dst_ip': random.choice(_SIM_DST_IPS),
        'src_port': src_port,
        'dst_port': dst_port,
        'protocol': protocol,
        'length': random.randint(40, 1500),
        'flags': random.choice(_SIM_FLAGS) if protocol in ('TCP', 'HTTP') else '',
        'ttl': random.choice([32, 64, 128, 255]),
        'window_size': random.randint(1024, 65535) if protocol == 'TCP' else None,
        'checksum': f'0x{random.randint(0, 0xFFFF):04x}',
        'seq_num': random.randint(0, 0xFFFFFFFF) if protocol == 'TCP' else None,
        'ack_num': random.randint(0, 0xFFFFFFFF) if protocol == 'TCP' else None,
        'timestamp': timezone.now().isoformat(),
    }


def _simulation_worker(user_id, duration, rate):
    """
    Background thread that pushes simulated packets to the WebSocket
    channel layer at approximately *rate* packets per second.
    """
    channel_layer = get_channel_layer()
    end_time = time.time() + duration
    interval = 1.0 / max(rate, 1)

    logger.info(f"Packet simulation started for user {user_id}: "
                f"duration={duration}s, rate={rate} pkt/s")

    while time.time() < end_time:
        # Check if we've been asked to stop
        with _simulation_lock:
            entry = _simulation_threads.get(user_id)
            if entry is None or entry.get('stop'):
                break

        pkt = _generate_simulated_packet()
        try:
            async_to_sync(channel_layer.group_send)('packets', {
                'type': 'packet_message',
                'data': pkt,
            })
        except Exception as e:
            logger.warning(f"Simulation broadcast error: {e}")

        time.sleep(interval + random.uniform(-interval * 0.2, interval * 0.2))

    # Clean up
    with _simulation_lock:
        _simulation_threads.pop(user_id, None)

    logger.info(f"Packet simulation ended for user {user_id}")


class SimulatePacketsView(APIView):
    """
    Start a simulated packet stream for the Packet Inspector.

    Launches a background thread that generates realistic fake packets
    and broadcasts them via the 'packets' WebSocket group, so the
    Packet Inspector page can display them without needing Scapy,
    Celery, or root privileges.

    POST body (all optional):
        duration: seconds to run (default 120, max 300)
        rate: packets per second (default 5, max 50)
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user_id = request.user.id
        duration = min(int(request.data.get('duration', 120)), 300)
        rate = min(int(request.data.get('rate', 5)), 50)

        with _simulation_lock:
            if user_id in _simulation_threads:
                return Response(
                    {'error': 'A packet simulation is already running.'},
                    status=status.HTTP_409_CONFLICT,
                )

            thread = threading.Thread(
                target=_simulation_worker,
                args=(user_id, duration, rate),
                daemon=True,
            )
            _simulation_threads[user_id] = {'thread': thread, 'stop': False}
            thread.start()

        return Response({
            'message': 'Packet simulation started.',
            'duration': duration,
            'rate': rate,
        }, status=status.HTTP_201_CREATED)


class StopSimulatePacketsView(APIView):
    """Stop a running packet simulation."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user_id = request.user.id

        with _simulation_lock:
            entry = _simulation_threads.get(user_id)
            if not entry:
                return Response(
                    {'error': 'No packet simulation is running.'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            entry['stop'] = True

        return Response({'message': 'Packet simulation stopping.'})
