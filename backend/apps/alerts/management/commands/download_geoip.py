"""
Management command to download the free MaxMind GeoLite2-City database.

Usage:
    # Using a MaxMind license key (register free at maxmind.com):
    python manage.py download_geoip --license-key YOUR_KEY

    # Using a public mirror (no key needed):
    python manage.py download_geoip --mirror
"""
import os
import gzip
import shutil
import tarfile
import tempfile
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


MAXMIND_URL = (
    "https://download.maxmind.com/app/geoip_download"
    "?edition_id=GeoLite2-City&license_key={key}&suffix=tar.gz"
)

# Public mirror maintained by the community (no key required).
MIRROR_URL = (
    "https://git.io/GeoLite2-City.mmdb"
)

DB_FILENAME = "GeoLite2-City.mmdb"


class Command(BaseCommand):
    help = "Download the MaxMind GeoLite2-City database for GeoIP lookups."

    def add_arguments(self, parser):
        parser.add_argument(
            "--license-key",
            type=str,
            default=None,
            help="MaxMind license key (free registration at maxmind.com).",
        )
        parser.add_argument(
            "--mirror",
            action="store_true",
            default=False,
            help="Download from a public mirror instead of MaxMind directly.",
        )

    def handle(self, *args, **options):
        dest_dir = str(settings.GEOIP_PATH)
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, DB_FILENAME)

        license_key = options.get("license_key")
        use_mirror = options.get("mirror")

        if not license_key and not use_mirror:
            raise CommandError(
                "Provide either --license-key YOUR_KEY (from maxmind.com) "
                "or --mirror to download from a public mirror."
            )

        if use_mirror:
            self._download_mirror(dest_path)
        else:
            self._download_maxmind(license_key, dest_dir, dest_path)

        if os.path.exists(dest_path):
            size_mb = os.path.getsize(dest_path) / (1024 * 1024)
            self.stdout.write(self.style.SUCCESS(
                f"GeoLite2-City.mmdb saved to {dest_path} ({size_mb:.1f} MB)"
            ))
        else:
            raise CommandError("Download completed but database file was not found.")

    def _download_mirror(self, dest_path):
        """Download the .mmdb directly from a public mirror."""
        self.stdout.write("Downloading GeoLite2-City.mmdb from public mirror...")
        try:
            urllib.request.urlretrieve(MIRROR_URL, dest_path)
        except Exception as e:
            raise CommandError(f"Mirror download failed: {e}")

    def _download_maxmind(self, license_key, dest_dir, dest_path):
        """Download and extract from MaxMind's official endpoint."""
        url = MAXMIND_URL.format(key=license_key)
        self.stdout.write("Downloading GeoLite2-City from MaxMind...")

        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            urllib.request.urlretrieve(url, tmp_path)

            # Extract .mmdb from the tarball
            with tarfile.open(tmp_path, "r:gz") as tar:
                for member in tar.getmembers():
                    if member.name.endswith(DB_FILENAME):
                        member.name = DB_FILENAME  # flatten path
                        tar.extract(member, dest_dir)
                        break
                else:
                    raise CommandError(
                        "Could not find GeoLite2-City.mmdb inside the downloaded archive."
                    )
        except tarfile.TarError as e:
            raise CommandError(f"Failed to extract archive: {e}")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
