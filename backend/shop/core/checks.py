"""Fail-closed startup validation and supported Django check registration."""
import os
from pathlib import Path
import stat
from django.core.checks import Error, register
from django.core.exceptions import ImproperlyConfigured

MODES = {'local', 'synthetic', 'bank-sandbox', 'production'}


def reject(message):
    import logging
    logging.getLogger('shop').warning('startup rejected', extra={'event': 'startup.rejected'})
    raise ImproperlyConfigured(message)


def validate_environment(env):
    mode = env.get('SHOP_ENV')
    if mode not in MODES:
        reject('SHOP_ENV must explicitly select a supported environment')
    if env.get('LIVE_PAYMENTS_ENABLED') != 'false':
        reject('Live payments must remain explicitly disabled')
    for key in ('PAYMENT_ADAPTER', 'MAIL_ADAPTER', 'STORAGE_ADAPTER'):
        if env.get(key) != 'fake':
            reject('Only explicitly selected fake adapters are implemented')
    if any(env.get(key) for key in ('BANK_ENDPOINT', 'BANK_API_KEY', 'SMTP_HOST', 'STORAGE_ENDPOINT',
                                  'SECRET_KEY', 'DATABASE_PASSWORD')):
        reject('Live endpoints and inline credentials are unavailable')
    if env.get('DEBUG', 'false') != 'false':
        reject('DEBUG must remain false')
    return mode


def runtime_secret_file(path, *, minimum=16, allowed_root=Path('/run/secrets/shop')):
    """Read only bounded private regular runtime files; errors contain no path/data."""
    try:
        candidate = Path(path)
        if not candidate.is_absolute() or candidate.parent != allowed_root or candidate.is_symlink():
            reject('Required runtime secret file is invalid')
        # Parent must be the actual runtime directory, never a symlink to checkout data.
        if allowed_root.resolve() != allowed_root:
            reject('Required runtime secret directory is invalid')
        fd = os.open(candidate, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            info = os.fstat(fd)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                    or stat.S_IMODE(info.st_mode) not in (0o400, 0o600) or not minimum <= info.st_size <= 4096):
                reject('Required runtime secret permissions or size are invalid')
            value = os.read(fd, 4097).decode('utf-8').strip()
            if not minimum <= len(value) <= 4096:
                reject('Required runtime secret length is invalid')
            return value
        finally:
            os.close(fd)
    except (OSError, TypeError, UnicodeError, ValueError):
        reject('Required runtime secret file is unavailable')


@register()
def safe_runtime_checks(app_configs, **kwargs):
    from django.conf import settings
    errors = []
    if settings.DEBUG or settings.LIVE_PAYMENTS_ENABLED is not False:
        errors.append(Error('Unsafe runtime switches', id='shop.E001'))
    if any(getattr(settings, key, None) != 'fake' for key in ('PAYMENT_ADAPTER', 'MAIL_ADAPTER', 'STORAGE_ADAPTER')):
        errors.append(Error('Only fake adapters are available', id='shop.E002'))
    if settings.SHOP_ENV not in MODES or '*' in settings.ALLOWED_HOSTS:
        errors.append(Error('Unsafe environment or host configuration', id='shop.E003'))
    return errors
