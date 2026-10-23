"""Separate local staff process. No production hostname or transport approval."""
from .local import *
ROOT_URLCONF='shop.staff_urls'
LOCAL_STAFF_ENABLED=True
LOCAL_STAFF_CAPTURE_ROOT=os.environ.get('SHOP_LOCAL_STAFF_CAPTURE_ROOT')
ALLOWED_HOSTS=['staff.localhost']
SESSION_COOKIE_NAME='shop_staff_sessionid'
CSRF_COOKIE_NAME='shop_staff_csrftoken'
SESSION_COOKIE_AGE=900
MIDDLEWARE=[MIDDLEWARE[0],'shop.access.staff_middleware.StaffHostMiddleware',*MIDDLEWARE[1:],
            'shop.access.staff_middleware.StaffMFAMiddleware']
TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','APP_DIRS':True}]
