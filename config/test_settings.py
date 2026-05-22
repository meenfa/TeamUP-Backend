# config/test_settings.py
"""
Test settings - Uses SQLite in-memory for fast, isolated tests
Your actual PostgreSQL database is completely untouched
"""

from .settings import *

# Override database for testing only
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # In-memory = super fast, no files created
    }
}

# Speed up password hashing (critical for test speed)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',  # Fast, not for production
]

# Optional: Skip migrations for even faster tests
import sys
if 'test' in sys.argv or 'pytest' in sys.modules:
    MIGRATION_MODULES = {
        app: None for app in INSTALLED_APPS
    }