"""Shared settings. Secrets and live integrations never come from a .env loader."""
import os
from shop.core.checks import validate_environment
SHOP_ENV = validate_environment(os.environ)
DEBUG = False
LIVE_PAYMENTS_ENABLED = False
PAYMENT_ADAPTER = MAIL_ADAPTER = STORAGE_ADAPTER = 'fake'
ROOT_URLCONF = 'shop.urls'
WSGI_APPLICATION = 'shop.wsgi.application'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','APP_DIRS':True,'OPTIONS':{'context_processors':['shop.catalog.presentation.customer_navigation']}}]
INSTALLED_APPS = ['django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'shop.core', 'shop.worker', 'shop.catalog', 'shop.access', 'shop.payments']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware',
              'shop.core.middleware.FormReferrerPolicyMiddleware',
              'shop.core.middleware.ValidHostMiddleware',
              'django.contrib.sessions.middleware.SessionMiddleware',
              'django.middleware.csrf.CsrfViewMiddleware',
              'django.contrib.auth.middleware.AuthenticationMiddleware',
              'shop.core.middleware.CustomerAccessContextMiddleware']
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = SHOP_ENV not in ('local','synthetic')
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1800
LOCAL_CAPTURE_ROOT = os.environ.get('SHOP_LOCAL_CAPTURE_ROOT') if SHOP_ENV in ('local','synthetic') else None
LOCAL_CHECKOUT_ARCHIVE_ROOT = os.environ.get('SHOP_LOCAL_CHECKOUT_ARCHIVE_ROOT') if SHOP_ENV in ('local','synthetic') else None
DATA_UPLOAD_MAX_MEMORY_SIZE = 32768
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
