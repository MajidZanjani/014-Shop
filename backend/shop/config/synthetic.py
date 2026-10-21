"""Explicit synthetic-only settings; no external provider credentials."""
from .base import *
from django.core.exceptions import ImproperlyConfigured
if SHOP_ENV != 'synthetic':
    raise ImproperlyConfigured('Synthetic settings require synthetic environment')
SECRET_KEY = 'synthetic-only-not-a-production-secret'
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
