from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from more_itertools import unique_justseen
from utilspie.collectionsutils import frozendict

if TYPE_CHECKING:
    from .page import Page
    from .volume import Volume


@dataclass(kw_only=True, frozen=True)
class Project:
    """
    A single documentation project that needs to be processed and rendered.
    """
    base: Path

    volumes: tuple[Volume, ...] = field(hash=False)
    primary_volume: Volume = field(hash=False, default=None)

    def __post_init__(self):
        for volume in self.volumes:
            object.__setattr__(volume, 'project', self)
        if self.primary_volume is None:
            object.__setattr__(self, 'primary_volume', self.volumes[0])

    def __repr__(self):
        return f'<{self.__class__.__name__}: {str(self.base)!r}>'

    def get_volume(self, key: str | tuple[str | None, str | None] | None = None) -> Volume:
        match key:
            case str() as autoprefix:
                for volume in self.volumes:
                    if volume.autoprefix == autoprefix:
                        return volume

            case (str() | None as lang, str() | None as codename):
                for volume in self.volumes:
                    if volume.lang == lang and volume.codename == codename:
                        return volume
            case None:
                assert len(self.volumes) == 1
                return self.volumes[0]

        raise KeyError(key)

    def get_translated_page(self, page: Page, lang_or_volume: str | Volume) -> Page:
        if isinstance(lang_or_volume, str):
            volume = self.get_volume((lang_or_volume, page.volume.codename))
        else:
            volume = lang_or_volume
        path_tr = volume.relative_root / page.path_in_volume
        page_tr = volume.pages_by_path[path_tr]
        return page_tr

    @cached_property
    def pages_by_path(self) -> dict[Path, Page]:
        pages_by_path = {}
        for volume in self.volumes:
            pages_by_path |= volume.pages_by_path
        return frozendict(pages_by_path)

    @cached_property
    def pages(self) -> tuple[Page, ...]:
        pages = sorted(self.pages_by_path.values(), key=lambda p: p.path)
        pages = list(unique_justseen(pages))
        return tuple(pages)
