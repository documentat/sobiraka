from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cache, cached_property
from pathlib import Path

from .project import Volume


@dataclass(frozen=True)
class Page:
    """
    Representation of a single source file in the documentation.

    During the processing by the :func:`.load_page()`, :func:`.process1()` and :func:`.process2()` functions, some of the page's fields may be altered.
    """
    volume: Volume
    """The :class:`.Volume` this page belongs to."""

    path: Path
    """Absolute path to the page source.
    
    :see also: :data:`relative_path`"""

    def __hash__(self):
        return hash((id(self.volume), self.path))

    def __repr__(self):
        path = self.path.relative_to(self.volume.project.root)
        return f'<{self.__class__.__name__}: {str(path)!r}>'

    def __lt__(self, other):
        assert isinstance(other, Page)
        return self.relative_path < other.relative_path

    @cached_property
    def relative_path(self) -> Path:
        """Path to the page source, relative to :data:`.Volume.root`."""
        return self.path.relative_to(self.volume.root)

    @cached_property
    def is_index(self) -> bool:
        return bool(re.fullmatch(r'0(-.*)? | (\d+-)?index', self.path.stem, flags=re.X))

    @cached_property
    def breadcrumbs(self) -> list[Page]:
        breadcrumbs: list[Page] = [self]
        while breadcrumbs[0].parent is not None:
            breadcrumbs.insert(0, breadcrumbs[0].parent)
        return breadcrumbs

    @cached_property
    def parent(self) -> Page | None:
        from . import EmptyPage

        if self.is_index:
            if isinstance(self, EmptyPage):
                if self.relative_path == Path('.'):
                    return None
                return self.volume.pages_by_path[self.relative_path.parent]
            else:
                if self.relative_path.parent == Path('.'):
                    return None
                return self.volume.pages_by_path[self.relative_path.parent.parent]
        else:
            return self.volume.pages_by_path[self.relative_path.parent]

    @cached_property
    def children(self) -> list[Page]:
        children: list[Page] = []
        for page in self.volume.pages:
            if page.parent is self:
                children.append(page)
        return children

    @cached_property
    def children_recursive(self) -> list[Page]:
        children: list[Page] = []
        for page in self.volume.pages:
            if page is not self and self in page.breadcrumbs:
                children.append(page)
        return children

    def _id_segment(self) -> str:
        if self.parent is None:
            return 'r'
        elif self.is_index:
            return re.sub(r'^(\d+-)?', '', self.relative_path.parent.stem)
        else:
            return re.sub(r'^(\d+-)?', '', self.relative_path.stem)

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
            parts.append(page._id_segment())
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
    def syntax(self) -> str:
        match self.path.suffix:
            case '.md':
                return 'markdown-smart'
            case '.rst':
                return 'rst-auto_identifiers'
            case _:  # pragma: no cover
                raise NotImplementedError(self.path.suffix)

    @cache
    def raw(self) -> str:
        return self.path.read_text('utf-8')