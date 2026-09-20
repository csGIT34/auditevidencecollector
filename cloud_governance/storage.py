"""Small immutable-object boundary. The local adapter performs no cloud calls."""
from contextlib import contextmanager
import os
from pathlib import Path
import re
import stat
from typing import Protocol
from uuid import uuid4


class ObjectStore(Protocol):
    def put_new(self, key: str, data: bytes) -> None:
        """Atomically publish bytes iff key is absent; never replace an object."""
    def read(self, key: str) -> bytes:
        """Read exactly one object or fail; never select a newer object."""
    def keys(self, prefix: str) -> list[str]:
        """List published object keys below a directory prefix."""


def parts(key):
    if not isinstance(key, str) or len(key) > 512:
        raise ValueError('Invalid object key')
    result = key.split('/')
    if any(not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}', p) or p in ('.', '..') for p in result):
        raise ValueError('Invalid object key')
    return result


class FileStore:
    """POSIX local storage; no symlink following, atomic hard-link publication.

    The operator must protect the root and its ancestors from hostile writers.
    Owner-only newly created directories/files do not make this a WORM archive.
    """
    def __init__(self, root):
        if not hasattr(os, 'O_NOFOLLOW') or os.open not in os.supports_dir_fd:
            raise OSError('Secure local adapter requires POSIX dir_fd and O_NOFOLLOW')
        self.root = Path(root).expanduser().absolute()
        if self.root.is_symlink():
            raise ValueError('Storage root must not be a symlink')
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if not self.root.is_dir():
            raise ValueError('Storage root must be a directory')

    @contextmanager
    def _parent(self, key, create=False):
        components = parts(key)
        fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for component in components[:-1]:
                if create:
                    try:
                        os.mkdir(component, 0o700, dir_fd=fd)
                        os.fsync(fd)
                    except FileExistsError:
                        pass
                child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = child
            yield fd, components[-1]
        finally:
            os.close(fd)

    def put_new(self, key, data):
        if not isinstance(data, bytes):
            raise TypeError('Object payload must be bytes')
        with self._parent(key, create=True) as (parent, leaf):
            temporary = '.pending-' + uuid4().hex
            fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600, dir_fd=parent)
            try:
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.link(temporary, leaf, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
                os.fsync(parent)
            finally:
                os.unlink(temporary, dir_fd=parent)

    def read(self, key):
        with self._parent(key) as (parent, leaf):
            fd = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            with os.fdopen(fd, 'rb') as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise ValueError('Object must be a regular file')
                return stream.read()

    def keys(self, prefix):
        components = parts(prefix.rstrip('/'))
        found = []
        def visit(fd, path):
            with os.scandir(fd) as entries:
                for entry in entries:
                    if entry.name.startswith('.pending-'):
                        continue
                    parts(entry.name)
                    key = path + '/' + entry.name
                    if entry.is_symlink():
                        raise ValueError('Symlink in storage')
                    if entry.is_dir(follow_symlinks=False):
                        child = os.open(entry.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                        try:
                            visit(child, key)
                        finally:
                            os.close(child)
                    elif entry.is_file(follow_symlinks=False):
                        found.append(key)
                    else:
                        raise ValueError('Non-regular object in storage')
        try:
            with self._parent('/'.join(components) + '/placeholder') as (fd, _):
                visit(fd, '/'.join(components))
        except FileNotFoundError:
            return []
        return sorted(found)
