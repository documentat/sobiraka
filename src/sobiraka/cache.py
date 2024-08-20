from __future__ import annotations

import pickle
import sys
from contextvars import ContextVar
from dataclasses import dataclass
from hashlib import sha256
from os.path import dirname
from shutil import rmtree

import diskcache
from checksumdir import dirhash

import sobiraka
from sobiraka.models import Page
from sobiraka.runtime import PageRuntime, RT
from sobiraka.utils import AbsolutePath


class Cache:
    def __getitem__(self, page: Page) -> PageCacheHandler:
        return PageCacheHandler(page)

    @staticmethod
    def save(key: str, value):
        try:
            cache_impl = _cache_impl_context.get()
        except LookupError:
            return

        if RT.DEBUG:
            print('SET', key, value, file=sys.stderr)
        cache_impl.set(key, value)

    @staticmethod
    def load(key: str):
        try:
            cache_impl = _cache_impl_context.get()
        except LookupError as exc:
            raise KeyError(key) from exc

        result = cache_impl.get(key)
        if result is None:
            raise KeyError(key)
        return result


@dataclass
class PageCacheHandler:
    page: Page

    # ------------------------------------------------------------------

    def _key_bytes(self, dependencies: set[Page]):
        return ':'.join((
            'BYTES',
            _hash(self.page.volume.config),
            str(self.page.path_in_volume),
            ','.join(f'({dep.path_in_volume}={_hash(dep.text)})' for dep in sorted(dependencies)) if RT.DEBUG
            else _hash(sorted(list((str(dep.path_in_volume), dep.text) for dep in dependencies))),
        ))

    def get_bytes(self, dependencies: set[Page]) -> bytes:
        key = self._key_bytes(dependencies)
        return CACHE.load(key)

    def set_bytes(self, page_rt: PageRuntime):
        key = self._key_bytes(page_rt.dependencies)
        CACHE.save(key, page_rt.bytes)


def _hash(data) -> str:
    if RT.DEBUG:
        if isinstance(data, str):
            return f'len={len(data)}'
        return sha256(pickle.dumps(data)).hexdigest()[:16]

    if isinstance(data, str):
        return sha256(data.encode('utf-8')).hexdigest()
    return sha256(pickle.dumps(data)).hexdigest()


def init_cache(cache_directory: AbsolutePath):
    app_fingerprint = dirhash(dirname(sobiraka.__file__),
                              hashfunc='sha256',
                              excluded_files=['**/__pycache__/*'],
                              excluded_extensions=['pyc'])
    app_fingerprint_file = cache_directory / 'fingerprint.txt'
    if cache_directory.exists():
        try:
            cache_fingerprint = app_fingerprint_file.read_text()
            assert cache_fingerprint == app_fingerprint
        except (FileNotFoundError, AssertionError):
            rmtree(cache_directory)
    cache_directory.mkdir(parents=True, exist_ok=True)
    app_fingerprint_file.write_text(app_fingerprint)

    _cache_impl_context.set(diskcache.Cache(str(cache_directory)))


CACHE = Cache()

_cache_impl_context: ContextVar[diskcache.Cache] = ContextVar('_cache_impl_context')
