"""Shared settings. Secrets and live integrations never come from a .env loader."""
import os
from shop.core.checks import validate_environment
SHOP_ENV = validate_environment(os.environ)
DEBUG = False
LIVE_PAYMENTS_ENABLED = False
PAYMENT_ADAPTER = MAIL_ADAPTER = STORAGE_ADAPTER = 'fake'
ROOT_URLCONF = 'shop.urls'
WSGI_APPLICATION = 'shop.wsgi.application'
INSTALLED_APPS = ['shop.core']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware']
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
DATABASES = {'default': {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': os.environ['DATABASE_NAME'], 'USER': os.environ['DATABASE_USER'],
    'PASSWORD': '', 'HOST': os.environ['DATABASE_HOST'], 'PORT': os.environ['DATABASE_PORT'],
    'CONN_MAX_AGE': 0,
    'OPTIONS': {'connect_timeout': 2, 'options': '-c statement_timeout=1000'},
}}

LOGGING = {
    'version': 1, 'disable_existing_loggers': False,
    'formatters': {'safe': {'()': 'shop.core.logging.SafeFormatter'}},
    'handlers': {'safe': {'class': 'logging.StreamHandler', 'formatter': 'safe'}},
    'root': {'handlers': ['safe'], 'level': 'INFO'},
    'loggers': {
        'django': {'handlers': [], 'propagate': True, 'level': 'INFO'},
        'django.server': {'handlers': [], 'propagate': True, 'level': 'INFO'},
        'shop': {'handlers': [], 'propagate': True, 'level': 'INFO'},
    },
}
