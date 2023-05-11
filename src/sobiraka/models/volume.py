from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

from more_itertools import unique_justseen
from utilspie.collectionsutils import frozendict

from .config import Config
from .emptypage import EmptyPage
from .page import Page
from .project import Project


# pylint: disable=too-many-instance-attributes
@dataclass(kw_only=True, frozen=True)
class Volume(Config):
    """
    A part of a :obj:`.Project`, identified uniquely by :data:`lang` and :data:`codename`.
    """

    project: Project = field(init=False, hash=False)
    """
    The project to which this volume belongs.
    """

    lang: str | None = None
    """
    The language code of this volume. See :obj:`
    """

    codename: str | None = None
    """
    Short identifier of the 
    """

    title: str | None = None
    """Human-readable title of the volume."""

    def __hash__(self):
        return hash((id(self.project), self.codename, self.lang))

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.autoprefix!r}>'

    def __lt__(self, other):
        assert isinstance(other, Volume)
        assert self.project is other.project
        volumes = self.project.volumes
        return volumes.index(self) < volumes.index(other)

    @property
    def autoprefix(self) -> str | None:
        return '/'.join(filter(None, (self.lang, self.codename))) or None

    @cached_property
    def pages_by_path(self) -> dict[Path, Page]:
        # pylint: disable=import-outside-toplevel

        pages: list[Page] = []
        pages_by_path: dict[Path, Page] = {}
        expected_paths: set[Path] = set()

        paths: set[Path] = set()
        for pattern in self.paths.include:
            paths |= set(self.root.glob(pattern))
        for pattern in self.paths.exclude:
            paths -= set(self.root.glob(pattern))

        for path in paths:
            path_in_project = path.relative_to(self.project.base)
            absolute_path = path.resolve()

            page = Page(self, absolute_path)
            pages.append(page)
            pages_by_path[path_in_project] = page
            if page.is_index():
                pages_by_path[path_in_project.parent] = page

            for parent in path_in_project.parents:
                if parent not in pages_by_path:
                    expected_paths.add(parent)
                if parent == self.relative_root:
                    break

        for expected_path in expected_paths:
            if expected_path not in pages_by_path:
                page = EmptyPage(self, self.project.base / expected_path)
                pages.append(page)
                pages_by_path[expected_path] = page

        return frozendict(sorted(pages_by_path.items()))

    @property
    def pages(self) -> tuple[Page, ...]:
        pages = sorted(self.pages_by_path.values(), key=lambda p: p.path)
        pages = list(unique_justseen(pages))
        return tuple(pages)

    @property
    def root(self) -> Path:
        """Absolute path to the root directory of the volume."""
        return self.paths.root

    @property
    def relative_root(self) -> Path:
        return self.paths.root.relative_to(self.project.base)

    @cached_property
    def max_level(self) -> int:
        """Maximum value of :obj:`.Page.level` in the volume. Used for calculating :obj:`.Page.antilevel`."""
        levels = tuple(page.level for page in self.pages)
        return max(levels) if levels else 0
