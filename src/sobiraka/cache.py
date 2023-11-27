from __future__ import annotations

import pickle
import sys
from contextvars import ContextVar
from dataclasses import dataclass
from hashlib import sha256
from os.path import dirname
from pathlib import Path
from shutil import rmtree

import diskcache
from checksumdir import dirhash

import sobiraka
from sobiraka.models import Page
from sobiraka.runtime import PageRuntime, RT


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

    def _key_preprocessed(self):
        return ':'.join((
            'PREPROCESSED',
            _hash(self.page.volume.config),
            str(self.page.path_in_volume),
            _hash(self.page.text),
        ))

    def get_preprocessed(self) -> PageRuntime:
        data = CACHE.load(self._key_preprocessed())
        return PageRuntime.load(data, self.page)

    def set_preprocessed(self, page_rt: PageRuntime):
        CACHE.save(self._key_preprocessed(), page_rt.dump())

    # ------------------------------------------------------------------

    def _key_dependencies(self):
        return ':'.join((
            'DEPENDENCIES',
            _hash(self.page.volume.config),
            str(self.page.path_in_volume),
            _hash(self.page.text),
        ))

    def get_dependencies(self) -> set[Page]:
        paths = CACHE.load(self._key_dependencies())
        return set(map(self.page.volume.pages_by_path.__getitem__, paths))

    def set_dependencies(self, dependencies: set[Page]):
        paths = list(p.path_in_volume for p in dependencies)
        CACHE.save(self._key_dependencies(), paths)

    # ------------------------------------------------------------------

    def _key_processed(self, dependencies: set[Page]):
        return ':'.join((
            'PROCESSED',
            _hash(self.page.volume.config),
            str(self.page.path_in_volume),
            _hash(self.page.text),
            ','.join(f'({dep.path_in_volume}={_hash(dep.text)})' for dep in sorted(dependencies)) if RT.DEBUG
            else _hash(sorted(list((str(dep.path_in_volume), dep.text) for dep in dependencies))),
        ))

    def get_processed(self, dependencies: set[Page]) -> PageRuntime:
        key = self._key_processed(dependencies)
        data = CACHE.load(key)
        return PageRuntime.load(data, self.page)

    def set_processed(self, page_rt: PageRuntime):
        key = self._key_processed(page_rt.dependencies)
        CACHE.save(key, page_rt.dump())

    # ------------------------------------------------------------------

    def _key_latex(self, dependencies: set[Page]):
        return ':'.join((
            'LATEX',
            _hash(self.page.volume.config),
            str(self.page.path_in_volume),
            ','.join(f'({dep.path_in_volume}={_hash(dep.text)})' for dep in sorted(dependencies)) if RT.DEBUG
            else _hash(sorted(list((str(dep.path_in_volume), dep.text) for dep in dependencies))),
        ))

    def get_latex(self, dependencies: set[Page]) -> bytes:
        key = self._key_latex(dependencies)
        return CACHE.load(key)

    def set_latex(self, page_rt: PageRuntime):
        key = self._key_latex(page_rt.dependencies)
        CACHE.save(key, page_rt.latex)


def _hash(data) -> str:
    if RT.DEBUG:
        if isinstance(data, str):
            return f'len={len(data)}'
        return sha256(pickle.dumps(data)).hexdigest()[:16]

    if isinstance(data, str):
        return sha256(data.encode('utf-8')).hexdigest()
    return sha256(pickle.dumps(data)).hexdigest()


def init_cache(cache_directory: Path):
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
