"""
GeoIP utility -- resolves IP addresses to geographic locations.

Resolution strategy (tried in order):
    1. MaxMind GeoLite2-City local database (most accurate).
    2. ip-api.com free API (45 req/min, needs network).
    3. Offline first-octet heuristic (instant, approximate).

This ensures the 3D globe and GeoIP map always display data even
when the MaxMind database file is not installed.
"""
import os
import logging
import ipaddress

from django.conf import settings

logger = logging.getLogger(__name__)

_reader = None
_reader_checked = False


def _get_reader():
    """Lazy-load GeoIP reader. Only attempts to open the file once."""
    global _reader, _reader_checked
    if _reader_checked:
        return _reader

    _reader_checked = True
    try:
        import geoip2.database
        db_path = os.path.join(settings.GEOIP_PATH, 'GeoLite2-City.mmdb')
        if os.path.exists(db_path):
            _reader = geoip2.database.Reader(db_path)
            logger.info("GeoIP database loaded successfully from %s", db_path)
        else:
            logger.warning(
                "GeoIP database not found at %s — will use fallback lookups",
                db_path,
            )
    except Exception as e:
        logger.error("Failed to load GeoIP database: %s", e)

    return _reader


def _is_private_ip(ip):
    """Check if IP is private/reserved."""
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_private or addr.is_loopback or addr.is_reserved
    except ValueError:
        return True


def _lookup_mmdb(ip_address):
    """Look up an IP using the local MaxMind .mmdb file."""
    reader = _get_reader()
    if reader is None:
        return None  # signal caller to try fallback

    try:
        response = reader.city(ip_address)
        return {
            'latitude': response.location.latitude,
            'longitude': response.location.longitude,
            'country': response.country.name or '',
            'city': response.city.name or '',
            'country_code': response.country.iso_code or '',
        }
    except Exception:
        return {}


def _lookup_ip_api(ip_address):
    """
    Fallback: query ip-api.com (free, no key needed, 45 req/min limit).
    Returns the same dict shape as _lookup_mmdb.
    """
    import urllib.request
    import json

    url = f"http://ip-api.com/json/{ip_address}?fields=status,country,countryCode,city,lat,lon"
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            data = json.loads(resp.read().decode())
        if data.get('status') == 'success':
            return {
                'latitude': data.get('lat'),
                'longitude': data.get('lon'),
                'country': data.get('country', ''),
                'city': data.get('city', ''),
                'country_code': data.get('countryCode', ''),
            }
    except Exception as e:
        logger.debug("ip-api.com lookup failed for %s: %s", ip_address, e)

    return {}


# ── Offline heuristic fallback ──────────────────────────────────────
# Maps first-octet ranges to approximate geographic regions so the
# 3D globe and GeoIP map display meaningful data even when neither the
# MaxMind database nor the ip-api.com service is available (e.g. during
# high-rate packet capture or offline development).
_FALLBACK_GEO = [
    # (first_octet_start, first_octet_end, lat, lng, country, city)
    (1, 9, 37.75, -122.42, 'United States', 'San Francisco'),
    (11, 15, 38.90, -77.04, 'United States', 'Washington'),
    (16, 30, 40.71, -74.01, 'United States', 'New York'),
    (31, 40, 51.51, -0.13, 'United Kingdom', 'London'),
    (41, 45, 6.52, 3.38, 'Nigeria', 'Lagos'),
    (46, 60, 48.86, 2.35, 'France', 'Paris'),
    (61, 80, 52.52, 13.41, 'Germany', 'Berlin'),
    (81, 95, 55.76, 37.62, 'Russia', 'Moscow'),
    (96, 110, 39.90, 116.41, 'China', 'Beijing'),
    (111, 125, 35.68, 139.65, 'Japan', 'Tokyo'),
    (126, 135, 37.57, 126.98, 'South Korea', 'Seoul'),
    (136, 150, 48.21, 16.37, 'Austria', 'Vienna'),
    (151, 160, -23.55, -46.63, 'Brazil', 'Sao Paulo'),
    (161, 170, 10.82, 106.63, 'Vietnam', 'Ho Chi Minh City'),
    (171, 180, 1.35, 103.82, 'Singapore', 'Singapore'),
    (181, 190, 50.11, 8.68, 'Germany', 'Frankfurt'),
    (191, 200, -33.87, 151.21, 'Australia', 'Sydney'),
    (201, 210, 19.43, -99.13, 'Mexico', 'Mexico City'),
    (211, 220, 37.57, 126.98, 'South Korea', 'Seoul'),
    (221, 230, 39.90, 116.41, 'China', 'Beijing'),
    (231, 240, 28.61, 77.21, 'India', 'New Delhi'),
    (241, 255, 52.37, 4.90, 'Netherlands', 'Amsterdam'),
]


def _fallback_heuristic(ip_address):
    """
    Estimate geolocation from the first octet of the IP address.
    Instant, no network calls, no rate limits.
    """
    try:
        first_octet = int(ip_address.split('.')[0])
    except (ValueError, IndexError):
        return {}

    for start, end, lat, lng, country, city in _FALLBACK_GEO:
        if start <= first_octet <= end:
            return {
                'latitude': lat,
                'longitude': lng,
                'country': country,
                'city': city,
                'country_code': '',
            }
    return {}


def lookup_ip(ip_address):
    """
    Look up geographic location for an IP address.

    Strategy:
        1. Skip private / reserved IPs (they have no meaningful geo data).
        2. Try the local MaxMind GeoLite2-City database.
        3. If the database file is missing, fall back to ip-api.com.
        4. If the API is unavailable, use an offline first-octet heuristic.

    Returns dict with: latitude, longitude, country, city, country_code
    Returns empty dict if lookup fails.
    """
    if _is_private_ip(ip_address):
        return {}

    # Try local database first
    result = _lookup_mmdb(ip_address)
    if result is not None:
        return result

    # Fallback to free API
    result = _lookup_ip_api(ip_address)
    if result:
        return result

    # Last resort: offline heuristic based on first octet
    return _fallback_heuristic(ip_address)
