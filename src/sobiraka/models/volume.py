from __future__ import annotations

from functools import cached_property

from sobiraka.utils import Location, RelativePath
from .config import Config
from .namingscheme import NamingScheme
from .page import Page
from .project import Project
from .source import Source


class Volume:
    """
    A part of a :obj:`.Project`, identified uniquely by :data:`lang` and :data:`codename`.
    """

    def __init__(self, lang: str | None, codename: str | None, config: Config):
        self.lang: str | None = lang
        self.codename: str | None = codename
        self.config: Config = config

        self.project: Project = None

    def __hash__(self):
        return hash(id(self))

    def __repr__(self):
        if self.autoprefix:
            return f'<{self.__class__.__name__}: {self.autoprefix!r}>'
        return f'<{self.__class__.__name__} (unnamed)>'

    def __lt__(self, other):
        assert isinstance(other, Volume)
        assert self.project is other.project
        volumes = self.project.volumes
        return volumes.index(self) < volumes.index(other)

    # ------------------------------------------------------------------------------------------------------------------
    # Project and configuration

    @property
    def autoprefix(self) -> str | None:
        return '/'.join(filter(None, (self.lang, self.codename))) or None

    @property
    def naming_scheme(self) -> NamingScheme:
        return self.config.paths.naming_scheme

    # ------------------------------------------------------------------------------------------------------------------
    # Pages and paths

    @property
    def root_path(self) -> RelativePath:
        return self.config.paths.root

    @cached_property
    def root(self) -> 'Source':
        from .source import make_source
        return make_source(self, self.config.paths.root, parent=None)

    @property
    def root_page(self) -> Page:
        return self.get_page_by_location('/')

    def get_page_by_location(self, location: Location | str) -> Page:
        for page in self.root.all_pages():
            if str(page.location) == str(location):
                return page
        raise KeyError(location)
