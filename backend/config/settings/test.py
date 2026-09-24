"""Test settings.

The default test database is PostgreSQL so tests exercise the production database
engine. A SQLite test fallback is available only for isolated local unit tests
when PostgreSQL is unavailable; it is not part of the application configuration.
"""

import os
import secrets

from .base import *  # noqa: F403


DEBUG = False
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(50)
SIMPLE_JWT["SIGNING_KEY"] = SECRET_KEY
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.PBKDF2PasswordHasher"]
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "1000/min",
    "user": "1000/min",
}

if os.getenv("TEST_DATABASE_ENGINE", "postgres").lower() == "sqlite":  # noqa: F405
    DATABASES = {  # noqa: F405
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BACKEND_DIR / "test.sqlite3",  # noqa: F405
        }
    }
else:
    DATABASES["default"]["TEST"] = {  # noqa: F405
        "NAME": os.getenv(  # noqa: F405
            "POSTGRES_TEST_DB", "test_superlative_classification"
        )
    }
