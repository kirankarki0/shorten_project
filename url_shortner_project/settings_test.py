"""
Test settings for URL Shortener
This file contains test-specific configurations
"""

from .settings import *

# Enable rate limiting for tests
RATELIMIT_ENABLE = True

# Use in-memory cache for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
}

# Disable debug for tests
DEBUG = False

# Use test database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable password hashing for faster tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable logging for tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
}

# Test-specific security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
