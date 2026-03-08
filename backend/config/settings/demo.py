"""
Demo-specific Django settings for 5-computer live demo.
Uses 3 separate PostgreSQL databases (free, premium, exclusive) and Redis.
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

# ── Redis channel layer for WebSocket broadcasting across LAN ──
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        },
    },
}

# ── Open for LAN access ──
ALLOWED_HOSTS = ['*']
CORS_ALLOW_ALL_ORIGINS = True

# ── Demo mode flag (enables alert fanout across databases) ──
DEMO_MODE = True

# ── Custom JWT auth for multi-database login ──
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apps.accounts.auth_backends.MultiDBJWTAuthentication',
    ),
}

# ── Email — console output in demo ──
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ── Add tier database middleware ──
MIDDLEWARE = MIDDLEWARE + [
    'config.middleware.TierDatabaseMiddleware',
]
