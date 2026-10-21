"""Bounded synthetic byte storage in a caller-owned private disposable directory."""
import os
from pathlib import Path
import re
import stat
import uuid
from django.conf import settings


class LocalStorage:
    def __init__(self, directory):
        if settings.SHOP_ENV not in {'local', 'synthetic'} or settings.STORAGE_ADAPTER != 'fake':
            raise ValueError('Synthetic storage unavailable')
        root = Path(directory)
        if not root.is_absolute() or root.is_symlink() or root.resolve() != root:
            raise ValueError('Invalid synthetic storage root')
        self.fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        info = os.fstat(self.fd)
        if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
            os.close(self.fd)
            raise ValueError('Synthetic storage root must be owned and private')
        self.owned = set()

    def __enter__(self): return self

    def __exit__(self, *args): os.close(self.fd)

    def put(self, value):
        if type(value) is not bytes or not 1 <= len(value) <= 1048576:
            raise ValueError('Invalid bounded synthetic object')
        key = uuid.uuid4().hex
        fd = os.open(key, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=self.fd)
        try:
            with os.fdopen(fd, 'wb') as output:
                output.write(value)
        except BaseException:
            os.unlink(key, dir_fd=self.fd)
            raise
        self.owned.add(key)
        return key

    def get(self, key):
        if not isinstance(key, str) or re.fullmatch('[0-9a-f]{32}', key) is None:
            raise ValueError('Invalid generated object identity')
        fd = os.open(key, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=self.fd)
        with os.fdopen(fd, 'rb') as source:
            info = os.fstat(source.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or not 1 <= info.st_size <= 1048576:
                raise ValueError('Invalid bounded synthetic object')
            value = source.read(1048577)
            if len(value) != info.st_size:
                raise ValueError('Synthetic object changed while reading')
            return value

    def reset(self):
        for key in tuple(self.owned):
            os.unlink(key, dir_fd=self.fd)
            self.owned.remove(key)
