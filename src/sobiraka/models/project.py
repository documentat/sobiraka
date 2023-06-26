from __future__ import annotations

from contextlib import suppress
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, overload

from more_itertools import unique_justseen
from utilspie.collectionsutils import frozendict

from .filesystem import FileSystem

if TYPE_CHECKING:
    from .page import Page
    from .volume import Volume


class Project:
    """
    A single documentation project that needs to be processed and rendered.
    """

    @overload
    def __init__(self, fs: FileSystem, volumes: tuple[Volume, ...]):
        ...

    @overload
    def __init__(self, fs: FileSystem, volumes: dict[Path, Volume]):
        ...

    def __init__(self, *args):
        self.fs: FileSystem
        self.volumes: tuple[Volume, ...]
        self.primary_volume: Volume
        self.manifest_path: Path | None = None

        match args:
            case FileSystem() as fs, tuple() as volumes:
                self.fs = fs
                self.volumes = volumes
                self.primary_volume = self.volumes[0]
                for volume in self.volumes:
                    volume.project = self

            case FileSystem() as fs, dict() as volumes:
                self.fs = fs
                self.volumes = tuple(volumes.values())
                self.primary_volume = self.volumes[0]
                for relative_root, volume in volumes.items():
                    volume.project = self
                    volume.relative_root = relative_root

            case _:
                raise TypeError(*args)

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.fs}>'

    @overload
    def get_volume(self, autoprefix: str) -> Volume:
        ...

    @overload
    def get_volume(self, lang: str | None, codename: str | None) -> Volume:
        ...

    @overload
    def get_volume(self) -> Volume:
        ...

    def get_volume(self, *args) -> Volume:
        match args:
            case str() as autoprefix,:
                for volume in self.volumes:
                    if volume.autoprefix == autoprefix:
                        return volume

            case str() | None as lang, str() | None as codename:
                for volume in self.volumes:
                    if volume.lang == lang and volume.codename == codename:
                        return volume

            case ():
                assert len(self.volumes) == 1
                return self.volumes[0]

        raise KeyError(args)

    def get_volume_by_path(self, path_in_project: Path) -> Volume:
        for volume in self.volumes:
            if volume.relative_root in path_in_project.parents:
                return volume
        raise KeyError(path_in_project)

    def get_translation(self, page: Page, lang_or_volume: str | Volume) -> Page:
        if isinstance(lang_or_volume, str):
            volume = self.get_volume(lang_or_volume, page.volume.codename)
        else:
            volume = lang_or_volume
        page_tr = volume.pages_by_path[page.path_in_volume]
        return page_tr

    def get_all_translations(self, page: Page) -> tuple[Page, ...]:
        translations: list[Page] = []
        for volume in self.volumes:
            if volume.codename == page.volume.codename:
                with suppress(KeyError):
                    page = volume.pages_by_path[volume.relative_root / page.path_in_volume]
                    translations.append(page)
        return tuple(translations)

    @cached_property
    def pages_by_path(self) -> dict[Path, Page]:
        pages_by_path = {}
        for volume in self.volumes:
            for path_in_volume, page in volume.pages_by_path.items():
                pages_by_path[volume.relative_root / path_in_volume] = page
        return frozendict(pages_by_path)

    @property  # TODO
    def pages(self) -> tuple[Page, ...]:
        pages = sorted(self.pages_by_path.values(), key=lambda p: p.path_in_project)
        pages = list(unique_justseen(pages))
        return tuple(pages)
