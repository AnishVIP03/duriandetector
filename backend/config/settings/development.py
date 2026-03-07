"""
Development-specific Django settings.
Uses SQLite and in-memory channel layer for easy local development.
"""
from .base import *

DEBUG = True

# SQLite for dev
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# In-memory channel layer for dev (no Redis required to start)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# CORS — allow all in dev
CORS_ALLOW_ALL_ORIGINS = True

# Email — console output in dev
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
