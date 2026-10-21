"""Local development has the same fake-only boundaries as synthetic execution."""
from .base import *
from django.core.exceptions import ImproperlyConfigured
if SHOP_ENV != 'local':
    raise ImproperlyConfigured('Local settings require local environment')
SECRET_KEY = 'local-only-not-a-production-secret'
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
