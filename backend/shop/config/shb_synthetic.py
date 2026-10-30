"""Explicit loopback-only SHB fixture demonstration, never production settings."""
from .synthetic import *
SHB_SYNTHETIC_FIXTURE = True
SHB_ALLOW_LOOPBACK_HTTP = True
SHB_PRIVATE_RELEASE_ROOT = os.environ.get('SHOP_SHB_PRIVATE_RELEASE_ROOT')
SHB_PRIVATE_RELEASE_SHA256 = os.environ.get('SHOP_SHB_PRIVATE_RELEASE_SHA256')
