from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cache, cached_property
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from ..syntax import Syntax
from ..version import Version

if TYPE_CHECKING:
    from sobiraka.models.volume import Volume

_META_PATTERN = re.compile(r'^---\n(.+\n)?---\n', re.DOTALL)


@dataclass(frozen=True)
class Page:
    """
    Representation of a single source file in the documentation.

    During the processing by the :func:`.load_page()`, :func:`.process1()` and :func:`.process2()` functions,
    some of the page's fields may be altered.
    """
    volume: Volume
    """The :class:`.Volume` this page belongs to."""

    path: Path
    """Absolute path to the page source.
    
    :see also: :data:`relative_path`"""

    def __hash__(self):
        return hash((id(self.volume), self.path))

    def __repr__(self):
        path = '/'.join(self.path.relative_to(self.volume.root).parts)
        match path:
            case self.volume.autoprefix:
                return f'<{self.__class__.__name__}: [{self.volume.autoprefix}]/{path}>'
            case Path('.'):
                return f'<{self.__class__.__name__}: />'
            case _:
                return f'<{self.__class__.__name__}: /{path}>'

    def __lt__(self, other):
        assert isinstance(other, Page), TypeError
        assert self.volume.project == other.volume.project
        return (self.volume, self.path_in_volume) < (other.volume, other.path_in_volume)

    @cached_property
    def path_in_project(self) -> Path:
        """Path to the page source, relative to :data:`.Project.root`."""
        return self.path.relative_to(self.volume.project.base)

    @cached_property
    def path_in_volume(self) -> Path:
        """Path to the page source, relative to :data:`.Volume.root`."""
        return self.path.relative_to(self.volume.root)

    def keys(self) -> tuple[Path, ...]:
        return (self.path_in_project,)

    def is_root(self) -> bool:
        return False

    @cached_property
    def breadcrumbs(self) -> tuple[Page, ...]:
        breadcrumbs: list[Page] = [self]
        while breadcrumbs[0].parent is not None:
            breadcrumbs.insert(0, breadcrumbs[0].parent)
        return tuple(breadcrumbs)

    @cached_property
    def parent(self) -> Page | None:
        if self.is_root():
            return None
        return self.volume.pages_by_path[self.path_in_project.parent]

    @cached_property
    def children(self) -> tuple[Page, ...]:
        children: list[Page] = []
        for page in self.volume.pages:
            if page.parent is self:
                children.append(page)
        return tuple(children)

    @cached_property
    def children_recursive(self) -> tuple[Page, ...]:
        children: list[Page] = []
        for page in self.volume.pages:
            if page is not self and self in page.breadcrumbs:
                children.append(page)
        return tuple(children)

    def id_segment(self) -> str:
        if self.is_root():
            return 'r'
        return re.sub(r'^(\d+-)?', '', self.path_in_project.stem)

    @cached_property
    def id(self) -> str:
        """
        Textual representation of :data:`breadcrumbs`, unique within the :class:`.Volume`.

        :examples:
            ``0-main.md`` → ``r`` \n
            ``2-company/5-about/0-index.md`` → ``r--company--about`` \n
            ``2-company/5-about/1-contacts.md`` → ``r--company--about--contacts``
        """
        parts: list[str] = []
        for page in self.breadcrumbs:
            parts.append(page.id_segment())
        return '--'.join(parts)

    @cached_property
    def level(self) -> int:
        """
        The depth of the page's location within its :class:`.Volume`.

        Equals to number of parts in the :data:`id` plus 1.
        """
        level = len(self.path.relative_to(self.volume.root).parts) + 1
        if self.path.stem == '0' or self.path.stem.startswith('0-'):
            level -= 1
        return level

    @property
    def antilevel(self) -> int:
        """
        A value that shows how far is this page's :data:`level` from the biggest level found in this :class:`.Volume`.

        For the pages with the biggest level, this value always equals to `1`.
        For other pages, it is always larger than `1`.

        :example: In a volume with only three pages, having levels `1`, `2`, `3`,
            their corresponding antilevels will be `3`, `2`, `1`.
        """
        return self.volume.max_level - self.level + 1

    @property
    def syntax(self) -> Syntax:
        return Syntax(self.path.suffix[1:])

    # pylint: disable=method-cache-max-size-none
    @cache
    def _raw(self) -> str:
        return self.path.read_text('utf-8')

    def text(self) -> str:
        return _META_PATTERN.sub('', self._raw())

    @cached_property
    def meta(self) -> PageMeta:
        meta = {}
        if m := _META_PATTERN.match(self._raw()):
            yaml_text = m.group(1).strip()
            if yaml_text:
                meta = yaml.safe_load(m.group(1))
        meta = PageMeta(meta)
        return meta


class PageMeta(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.version: Version | None = None
        if 'version' in self:
            self.version = Version.parse(str(self['version']))
