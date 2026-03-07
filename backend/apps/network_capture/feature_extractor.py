"""
Feature extraction from raw network packets.
Converts Scapy packets into numerical feature vectors for ML inference.
"""
import time
import math
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# Protocol number mapping
PROTOCOL_MAP = {
    'TCP': 6, 'UDP': 17, 'ICMP': 1, 'HTTP': 6,
    'DNS': 17, 'SSH': 6, 'FTP': 6, 'OTHER': 0,
}

# TCP flags mapping
FLAG_MAP = {
    'F': 1, 'S': 2, 'R': 4, 'P': 8,
    'A': 16, 'U': 32, 'E': 64, 'C': 128,
}


class PacketFeatureExtractor:
    """
    Extracts ML features from Scapy packets.
    Maintains state for flow-level features (connection count, inter-arrival time).
    """

    def __init__(self):
        self._last_packet_time = {}  # src_ip -> last timestamp
        self._connection_counts = defaultdict(int)  # src_ip -> count in window
        self._port_history = defaultdict(set)  # src_ip -> set of dst_ports
        self._window_start = time.time()
        self._window_size = 60  # 1-minute sliding window

    def _reset_window_if_needed(self):
        """Reset counters if window has expired."""
        now = time.time()
        if now - self._window_start > self._window_size:
            self._connection_counts.clear()
            self._port_history.clear()
            self._window_start = now

    def _calculate_port_entropy(self, src_ip):
        """Calculate Shannon entropy of destination ports for a source IP."""
        ports = self._port_history.get(src_ip, set())
        if len(ports) <= 1:
            return 0.0
        total = len(ports)
        entropy = -sum((1 / total) * math.log2(1 / total) for _ in ports)
        return round(entropy, 4)

    def extract(self, packet):
        """
        Extract feature vector from a Scapy packet.
        Returns: dict with raw info + feature vector list, or None if not IP packet.
        """
        try:
            from scapy.layers.inet import IP, TCP, UDP, ICMP

            if not packet.haslayer(IP):
                return None

            self._reset_window_if_needed()

            ip_layer = packet[IP]
            src_ip = ip_layer.src
            dst_ip = ip_layer.dst
            protocol = 'OTHER'
            src_port = 0
            dst_port = 0
            tcp_flags = 0
            ttl = ip_layer.ttl
            packet_length = len(packet)

            if packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                src_port = tcp_layer.sport
                dst_port = tcp_layer.dport
                protocol = 'TCP'
                # Convert flags
                flags_str = str(tcp_layer.flags)
                tcp_flags = sum(FLAG_MAP.get(f, 0) for f in flags_str)
                # Detect HTTP
                if dst_port in (80, 8080, 8000) or src_port in (80, 8080, 8000):
                    protocol = 'HTTP'
                elif dst_port == 22 or src_port == 22:
                    protocol = 'SSH'
                elif dst_port == 21 or src_port == 21:
                    protocol = 'FTP'
            elif packet.haslayer(UDP):
                udp_layer = packet[UDP]
                src_port = udp_layer.sport
                dst_port = udp_layer.dport
                protocol = 'UDP'
                if dst_port == 53 or src_port == 53:
                    protocol = 'DNS'
            elif packet.haslayer(ICMP):
                protocol = 'ICMP'

            # Flow features
            now = time.time()
            inter_arrival = 0.0
            if src_ip in self._last_packet_time:
                inter_arrival = now - self._last_packet_time[src_ip]
            self._last_packet_time[src_ip] = now

            self._connection_counts[src_ip] += 1
            self._port_history[src_ip].add(dst_port)

            connection_count = self._connection_counts[src_ip]
            port_entropy = self._calculate_port_entropy(src_ip)

            # Byte rate (approximate)
            byte_rate = packet_length / max(inter_arrival, 0.001)

            # Feature vector (must match FEATURE_NAMES in ml_engine)
            feature_vector = [
                packet_length,
                ttl,
                src_port,
                dst_port,
                PROTOCOL_MAP.get(protocol, 0),
                tcp_flags,
                inter_arrival,
                byte_rate,
                connection_count,
                port_entropy,
            ]

            # Raw payload (first 200 bytes as hex)
            raw_payload = ''
            if packet.haslayer(TCP) or packet.haslayer(UDP):
                try:
                    payload = bytes(packet.payload.payload.payload)
                    if payload:
                        raw_payload = payload[:200].hex()
                except Exception:
                    pass

            return {
                'src_ip': src_ip,
                'dst_ip': dst_ip,
                'src_port': src_port,
                'dst_port': dst_port,
                'protocol': protocol,
                'packet_length': packet_length,
                'ttl': ttl,
                'flags': str(tcp_flags),
                'inter_arrival_time': round(inter_arrival, 6),
                'feature_vector': feature_vector,
                'raw_payload': raw_payload,
                'timestamp': now,
            }
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            return None
