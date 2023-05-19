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

    def __post_init__(self):
        for volume in self.volumes:
            object.__setattr__(volume, 'project', self)

    def __repr__(self):
        return f'<{self.__class__.__name__}: {str(self.base)!r}>'

    def get_volume(self, autoprefix: str | None = None) -> Volume:
        for volume in self.volumes:
            if volume.autoprefix == autoprefix:
                return volume
        raise KeyError

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
