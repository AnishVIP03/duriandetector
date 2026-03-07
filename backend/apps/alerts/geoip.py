"""
GeoIP utility — resolves IP addresses to geographic locations.
Uses MaxMind GeoLite2 database.
"""
import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

_reader = None


def _get_reader():
    """Lazy-load GeoIP reader."""
    global _reader
    if _reader is not None:
        return _reader

    try:
        import geoip2.database
        db_path = os.path.join(settings.GEOIP_PATH, 'GeoLite2-City.mmdb')
        if os.path.exists(db_path):
            _reader = geoip2.database.Reader(db_path)
            logger.info("GeoIP database loaded successfully")
        else:
            logger.warning(f"GeoIP database not found at {db_path}")
    except Exception as e:
        logger.error(f"Failed to load GeoIP database: {e}")

    return _reader


def lookup_ip(ip_address):
    """
    Look up geographic location for an IP address.

    Returns dict with: latitude, longitude, country, city, country_code
    Returns empty dict if lookup fails.
    """
    # Skip private/local IPs
    if _is_private_ip(ip_address):
        return {}

    reader = _get_reader()
    if reader is None:
        return {}

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


def _is_private_ip(ip):
    """Check if IP is private/reserved."""
    import ipaddress
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_private or addr.is_loopback or addr.is_reserved
    except ValueError:
        return True
