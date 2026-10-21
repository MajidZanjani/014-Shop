"""Bounded root-owned operator records; no record provisioning or refresh."""
import json
import os
from pathlib import Path
import re
import stat
from guard import require


def unique_fields(pairs):
    result = {}
    for key,value in pairs:
        require(key not in result)
        result[key] = value
    return result


def load_control(filename, validator):
    """Walk root-owned, non-writable ancestors by FD; reject symlinks."""
    require(isinstance(filename,str) and re.fullmatch(r"[a-z][a-z0-9-]*\.json",filename))
    path = Path("/srv/shop/control")/filename
    directory = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in path.parts[1:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                              dir_fd=directory)
            os.close(directory)
            directory = next_fd
            info = os.fstat(directory)
            require(info.st_uid == 0 and not info.st_mode & 0o022)
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=directory)
        try:
            info = os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_uid == 0
                    and not info.st_mode & 0o022 and info.st_size <= 32768)
            data = os.read(fd, 32769)
            require(len(data) <= 32768)
            return validator(json.loads(data,object_pairs_hook=unique_fields))
        finally:
            os.close(fd)
    finally:
        os.close(directory)

