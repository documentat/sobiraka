from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar, final

from sobiraka.models import Document, Page, Project
from .builder import Builder
from .processor import Processor
from .theme import Theme

P = TypeVar('P', bound=Processor)
T = TypeVar('T', bound=Theme)


class ProjectBuilder(Builder, Generic[P], metaclass=ABCMeta):
    """
    A builder that works with the whole project at once.
    Each document can still have its own `Processor`, though.
    """

    def __init__(self, project: Project):
        Builder.__init__(self)

        self.project: Project = project
        self.processors: dict[Document, P] = {}

        for document in project.documents:
            self.processors[document] = self.init_processor(document)

    @final
    def get_project(self) -> Project:
        return self.project

    @final
    def get_documents(self) -> tuple[Document, ...]:
        return self.project.documents

    @final
    def get_pages(self) -> tuple[Page, ...]:
        return self.project.pages

    @final
    def get_processor_for_page(self, page: Page) -> P:
        return self.processors[page.document]

    @abstractmethod
    def init_processor(self, document: Document) -> P: ...


class ThemeableProjectBuilder(ProjectBuilder[P], Generic[P, T], metaclass=ABCMeta):
    def __init__(self, project: Project):
        super().__init__(project)

        self.themes: dict[Document, T] = {}
        for document in self.project.documents:
            self.themes[document] = self.init_theme(document)

    @abstractmethod
    def init_theme(self, document: Document) -> T: ...
