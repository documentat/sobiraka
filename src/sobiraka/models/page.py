from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cache, cached_property
from pathlib import Path

from .book import Book


@dataclass(frozen=True)
class Page:
    """
    Representation of a single source file in the documentation.

    During the processing by the :func:`.load_page()`, :func:`.process1()` and :func:`.process2()` functions, some of the page's fields may be altered.
    """
    book: Book
    """The :class:`.Book` this page belongs to."""

    path: Path
    """Absolute path to the page source, relative to :data:`.Book.root`.
    
    :see also: :data:`relative_path`"""

    def __repr__(self):
        return f'<Page: {str(self.relative_path)!r}>'

    def __lt__(self, other):
        assert isinstance(other, Page)
        return self.relative_path < other.relative_path

    @cached_property
    def relative_path(self) -> Path:
        """Path to the page source, relative to :data:`.Book.root`."""
        return self.path.relative_to(self.book.root)

    @cached_property
    def is_index(self) -> bool:
        return bool(re.fullmatch(r'0(-.*)? | (\d+-)?index', self.path.stem, flags=re.X))

    @cached_property
    def breadcrumbs(self) -> list[Page]:
        parents: tuple[Path, ...] = *reversed(self.relative_path.parents), self.relative_path
        if self.is_index:
            parents = parents[:-1]
        breadcrumbs: list[Page] = []
        for parent in parents:
            breadcrumbs.append(self.book.pages_by_path[parent])
        return breadcrumbs

    @cached_property
    def parent(self) -> Page | None:
        if self.is_index:
            return self.book.pages_by_path[self.relative_path.parent.parent]
        else:
            return self.book.pages_by_path[self.relative_path.parent]

    @cached_property
    def children(self) -> list[Page]:
        children: list[Page] = []
        for page in self.book.pages:
            if page.parent is self:
                children.append(page)
        return children

    @cached_property
    def children_recursive(self) -> list[Page]:
        children: list[Page] = []
        for page in self.book.pages:
            if page is not self and self in page.breadcrumbs:
                children.append(page)
        return children

    @cached_property
    def id(self) -> str:
        """
        Textual representation of :data:`breadcrumbs`, unique within the :class:`.Book`.

        :examples:
            ``0-main.md`` → ``r`` \n
            ``2-company/5-about/0-index.md`` → ``r--company--about`` \n
            ``2-company/5-about/1-contacts.md`` → ``r--company--about--contacts``
        """
        parts: list[str] = []
        for page in self.breadcrumbs:
            path = page.relative_path
            if page.is_index:
                path = path.parent
            if path == Path('.'):
                parts.append('r')
            else:
                parts.append(re.sub(r'^(\d+-)?', '', path.stem))
        return '--'.join(parts)

    @cached_property
    def level(self) -> int:
        """
        The depth of the page's location within its :class:`.Book`.

        Equals to number of parts in the :data:`id` plus 1.
        """
        level = len(self.relative_path.parts) + 1
        if self.path.stem == '0' or self.path.stem.startswith('0-'):
            level -= 1
        return level

    @property
    def antilevel(self) -> int:
        """
        A value that shows how far is this page's :data:`level` from the biggest level found in this :class:`.Book`.

        For the pages with the biggest level, this value always equals to `1`.
        For other pages, it is always larger than `1`.

        :example: In a book with only three pages, having levels `1`, `2`, `3`,
            their corresponding antilevels will be `3`, `2`, `1`.
        """
        return self.book.max_level - self.level + 1

    @property
    def syntax(self) -> str:
        match self.path.suffix:
            case '.md':
                return 'markdown'
            case '.rst':
                return 'rst-auto_identifiers'
            case _:  # pragma: no cover
                raise NotImplementedError(self.path.suffix)

    @cache
    def raw(self) -> str:
        return self.path.read_text('utf-8')