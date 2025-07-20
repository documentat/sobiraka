from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, overload

from sobiraka.utils import RelativePath
from .filesystem import FileSystem

if TYPE_CHECKING:
    from .document import Document
    from .page import Page


class Project:
    """
    A single documentation project that needs to be processed and rendered.
    """

    def __init__(self, fs: FileSystem, documents: tuple[Document, ...], primary_language: str = None):
        self.fs: FileSystem = fs
        self.documents: tuple[Document, ...] = documents
        for document in self.documents:
            document.project = self

        self.primary_language: str | None = primary_language

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.fs}>'

    @overload
    def get_document(self, autoprefix: str) -> Document:
        ...

    @overload
    def get_document(self, lang: str | None, codename: str | None) -> Document:
        ...

    @overload
    def get_document(self) -> Document:
        ...

    def get_document(self, *args) -> Document:
        match args:
            case str() | None as autoprefix,:
                for document in self.documents:
                    if document.autoprefix == autoprefix:
                        return document

            case str() | None as lang, str() | None as codename:
                for document in self.documents:
                    if document.lang == lang and document.codename == codename:
                        return document

            case ():
                assert len(self.documents) == 1
                return self.documents[0]

        raise KeyError(*args)

    def get_document_by_path(self, path_in_project: RelativePath) -> Document:
        for document in self.documents:
            if document.root_path in path_in_project.parents:
                return document
        raise KeyError(path_in_project)

    def get_translation(self, page: Page, lang: str) -> Page:
        document = self.get_document(lang, page.document.codename)
        page_tr = document.get_page_by_location(page.location)
        return page_tr

    def get_all_translations(self, page: Page) -> tuple[Page, ...]:
        translations: list[Page] = []
        for document in self.documents:
            if document.codename == page.document.codename:
                with suppress(KeyError):
                    page = document.get_page_by_location(page.location)
                    translations.append(page)
        return tuple(translations)
