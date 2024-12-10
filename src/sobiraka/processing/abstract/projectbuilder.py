from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar, final

from sobiraka.models import Page, Project, Volume
from .builder import Builder
from .processor import Processor
from .theme import Theme

P = TypeVar('P', bound=Processor)
T = TypeVar('T', bound=Theme)


class ProjectBuilder(Builder, Generic[P], metaclass=ABCMeta):
    """
    A builder that works with the whole project at once.
    Each volume can still have its own `Processor`, though.
    """

    def __init__(self, project: Project):
        Builder.__init__(self)

        self.project: Project = project
        self.processors: dict[Volume, P] = {}

        for volume in project.volumes:
            self.processors[volume] = self.init_processor(volume)

    @final
    def get_project(self) -> Project:
        return self.project

    @final
    def get_volumes(self) -> tuple[Volume, ...]:
        return self.project.volumes

    @final
    def get_pages(self) -> tuple[Page, ...]:
        return self.project.pages

    @final
    def get_processor_for_page(self, page: Page) -> P:
        return self.processors[page.volume]

    @abstractmethod
    def init_processor(self, volume: Volume) -> P: ...


class ThemeableProjectBuilder(ProjectBuilder[P], Generic[P, T], metaclass=ABCMeta):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.themes: dict[Volume, T] = {}
        for volume in self.project.volumes:
            self.themes[volume] = self.init_theme(volume)

    @abstractmethod
    def init_theme(self, volume: Volume) -> T: ...
