from __future__ import annotations

import re
from functools import cached_property
from pathlib import Path
from typing import Awaitable

from panflute import Doc

from . import Href
from .book import Book
from .error import ProcessingError


class Page:
    """
    Representation of a single source file in the documentation.

    During the processing by the :func:`.load_page()`, :func:`.process1()` and :func:`.process2()` functions, some of the page's fields may be altered.
    """

    def __init__(self, book: Book, path: Path):
        """
        :param book: The :class:`.Book` to which this page belongs.
        :param path: The source path of the page,
        """

        self.book: Book = book
        """The :class:`.Book` this page belongs to."""

        self.path: Path = path
        """Absolute path to the page source, relative to :data:`.Book.root`.
        
        :see also: :data:`relative_path`"""

        self.doc: Doc | None = None
        """The document tree, as parsed by `Pandoc <https://pandoc.org/>`_ and `Panflute <http://scorreia.com/software/panflute/>`_.
        
        Do not rely on this value until :data:`loaded` is triggered.
        """

        self.title: str | None = None
        """Page title.
        
        Do not rely on this value until :data:`processed1` is triggered."""

        self.links: list[Href] = []
        """All links present on the page, both internal and external.
        
        Do not rely on this value until :data:`processed1` is triggered."""

        self.anchors: dict[str, list[str]] = {}
        """Dictionary containing anchors and corresponding readable titles.
        
        Note that sometime a user leaves anchors empty or specifies identical anchors for multiple headers by mistake.
        However, this is not considered a critical error as long as no page contains links to this anchor.
        For that reason, all the titles for an anchor are stored as a list (in order of appearance on the page),
        and it is up to :func:`.process2_link()` to report an error if necessary.
        """

        self.errors: set[ProcessingError] = set()

        self.process2_tasks: list[Awaitable] = []
        """:meta private:"""

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
        Unique identifier of the page within its :class:`.Book`, based on :data:`relative_path`.

        From each part of the path, a numerical prefix is removed. From the last part, the suffix is removed.
        Additionally, if the very last part had numerical prefix ``0-``, the whole part is removed from the result.

        The path separator is replaced by ``--``.

        :examples:
            ``2-company/5-about/0-index.md`` → ``company--about`` \n
            ``2-company/5-about/1-contacts.md`` → ``company--about--contacts``
        """
        parts = list(self.relative_path.with_suffix('').parts)
        if parts[-1] == '0' or parts[-1].startswith('0-'):
            parts = parts[:-1]
        for i, part in enumerate(parts):
            parts[i] = re.sub(r'^(\d+-)?', '', part)
        return '--' + '--'.join(parts)

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