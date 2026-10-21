"""Synthetic development only. No production configuration or external adapters."""
import os
SECRET_KEY = "synthetic-only-not-a-production-secret"
DEBUG = False
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
ROOT_URLCONF = "shop.urls"
WSGI_APPLICATION = "shop.wsgi.application"
INSTALLED_APPS = []
MIDDLEWARE = ["django.middleware.security.SecurityMiddleware"]
USE_TZ = True
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": os.environ["DATABASE_NAME"],
    "USER": os.environ["DATABASE_USER"],
    "PASSWORD": "",
    "HOST": os.environ["DATABASE_HOST"],
    "PORT": os.environ["DATABASE_PORT"],
    "CONN_MAX_AGE": 0,
    "OPTIONS": {"connect_timeout": 2, "options": "-c statement_timeout=1000"},
}}
