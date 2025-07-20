from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar, final

from sobiraka.models import Document, Page, Project
from .builder import Builder
from .processor import Processor
from .theme import Theme

P = TypeVar('P', bound=Processor)
T = TypeVar('T', bound=Theme)


class DocumentBuilder(Builder, Generic[P], metaclass=ABCMeta):
    """
    A builder that works with an individual document.
    """

    def __init__(self, document: Document):
        super().__init__()
        self.document: Document = document
        self.processor: P = self.init_processor()

    @final
    def get_project(self) -> Project:
        return self.document.project

    @final
    def get_documents(self) -> tuple[Document, ...]:
        return self.document,

    @final
    def get_pages(self) -> tuple[Page, ...]:
        return self.document.pages

    @final
    def get_processor_for_page(self, page: Page) -> P:
        return self.processor

    @abstractmethod
    def init_processor(self) -> P: ...


class ThemeableDocumentBuilder(DocumentBuilder[P], Generic[P, T], metaclass=ABCMeta):
    def __init__(self, document: Document):
        super().__init__(document)
        self.theme: T = self.init_theme()

    @abstractmethod
    def init_theme(self) -> T: ...
