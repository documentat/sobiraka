from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar, final

from sobiraka.models import Page, Project, Volume
from .builder import Builder
from .processor import Processor
from .theme import Theme

P = TypeVar('P', bound=Processor)
T = TypeVar('T', bound=Theme)


class VolumeBuilder(Builder, Generic[P], metaclass=ABCMeta):
    """
    A builder that works with an individual volume.
    """

    def __init__(self, volume: Volume, **kwargs):
        Builder.__init__(self, **kwargs)
        self.volume: Volume = volume
        self.processor: P = self.init_processor()

    @final
    def get_project(self) -> Project:
        return self.volume.project

    @final
    def get_volumes(self) -> tuple[Volume, ...]:
        return self.volume,

    @final
    def get_pages(self) -> tuple[Page, ...]:
        return self.volume.pages

    @final
    def get_processor_for_page(self, page: Page) -> P:
        return self.processor

    @abstractmethod
    def init_processor(self) -> P: ...


class ThemeableVolumeBuilder(VolumeBuilder[P], Generic[P, T], metaclass=ABCMeta):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.theme: T = self.init_theme()

    @abstractmethod
    def init_theme(self) -> T: ...
