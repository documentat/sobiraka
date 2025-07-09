from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, overload

from sobiraka.models import FileSystem
from sobiraka.utils import RelativePath

if TYPE_CHECKING:
    from .page import Page
    from .volume import Volume


class Project:
    """
    A single documentation project that needs to be processed and rendered.
    """

    def __init__(self, fs: FileSystem, volumes: tuple[Volume, ...], primary_language: str = None):
        self.fs: FileSystem = fs
        self.volumes: tuple[Volume, ...] = volumes
        for volume in self.volumes:
            volume.project = self

        self.primary_language: str | None = primary_language

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
            case str() | None as autoprefix,:
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

        raise KeyError(*args)

    def get_volume_by_path(self, path_in_project: RelativePath) -> Volume:
        for volume in self.volumes:
            if volume.root_path in path_in_project.parents:
                return volume
        raise KeyError(path_in_project)

    def get_translation(self, page: Page, lang: str) -> Page:
        volume = self.get_volume(lang, page.volume.codename)
        page_tr = volume.get_page_by_location(page.location)
        return page_tr

    def get_all_translations(self, page: Page) -> tuple[Page, ...]:
        translations: list[Page] = []
        for volume in self.volumes:
            if volume.codename == page.volume.codename:
                with suppress(KeyError):
                    page = volume.get_page_by_location(page.location)
                    translations.append(page)
        return tuple(translations)
