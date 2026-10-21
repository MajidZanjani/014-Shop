"""Production-shaped and bank-sandbox modes; live effects remain unavailable."""
from .base import *
from shop.core.checks import runtime_secret_file
from django.core.exceptions import ImproperlyConfigured
if SHOP_ENV not in {'production', 'bank-sandbox'}:
    raise ImproperlyConfigured('Production settings require explicit production-shaped environment')
SECRET_KEY = runtime_secret_file(os.environ.get('SECRET_KEY_FILE'), minimum=50)
# Gate every Django connection, including migrate and no-database maintenance.
DATABASES['default']['ENGINE'] = 'shop.db.unqualified'
DATABASES['default']['PASSWORD'] = runtime_secret_file(os.environ.get('DATABASE_PASSWORD_FILE'))
if not DATABASES['default']['HOST'] or not DATABASES['default']['USER'] or not DATABASES['default']['NAME']:
    raise ImproperlyConfigured('Explicit shop database identity is required')
ALLOWED_HOSTS = ['shop.xspi.pro', 'shop-admin.xspi.pro']
CSRF_TRUSTED_ORIGINS = ['https://shop.xspi.pro', 'https://shop-admin.xspi.pro']
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
# No proxy-header trust until the exact ingress contract is qualified.
