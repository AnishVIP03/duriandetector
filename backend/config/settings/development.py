"""
Development-specific Django settings.
Uses PostgreSQL with multi-database architecture and Redis channel layer.
"""
from .base import *

DEBUG = True

# ── Three separate PostgreSQL databases ──
_DB_COMMON = {
    'ENGINE': 'django.db.backends.postgresql',
    'USER': 'demo_user',
    'PASSWORD': 'demo_password',
    'HOST': '127.0.0.1',
    'PORT': '5432',
}

DATABASES = {
    'default': {**_DB_COMMON, 'NAME': 'duriandetector_free'},
    'free_db': {**_DB_COMMON, 'NAME': 'duriandetector_free'},
    'premium_db': {**_DB_COMMON, 'NAME': 'duriandetector_premium'},
    'exclusive_db': {**_DB_COMMON, 'NAME': 'duriandetector_exclusive'},
}

# ── Multi-database routing ──
DATABASE_ROUTERS = ['config.db_router.TierDatabaseRouter']

# CORS — allow all in dev
CORS_ALLOW_ALL_ORIGINS = True

# Email — console output in dev
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
