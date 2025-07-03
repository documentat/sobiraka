from functools import cached_property
from importlib.resources import files
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from more_itertools import one
from typing_extensions import override

from sobiraka.utils import RelativePath, convert_or_none
from .indexsourcefile import IndexSourceFile
from .source import IdentifierResolutionError, Source
from .sourcefile import SourceFile
from ..filesystem import FileSystem
from ..href import PageHref
from ..page import Page, PageMeta
from ..syntax import Syntax
from ..version import Version

NAV_FILENAME = '_nav.yaml'
SCHEMA = yaml.safe_load((files('sobiraka') / 'files' / 'sobiraka-nav.yaml').read_text())


class SourceNav(Source):

    @override
    async def generate_child_sources(self):
        from . import make_source
        fs = self.volume.project.fs

        child_sources = []

        items = self._data.get('items', ())
        items = list(map(self._parse_item, items))
        for subpath, options in items:
            child = make_source(self.volume, self.path_in_project / subpath, parent=self)
            if options:
                assert isinstance(child, SourceFile), 'Custom metadata is only applicable to a SourceFile'
                child.base_meta = options

            child_sources.append(child)

        for syntax in Syntax:
            index_path = self.path_in_project / f'_index.{syntax.value}'
            if fs.exists(index_path):
                child_sources.insert(0, IndexSourceFile(self.volume, index_path, parent=self))
                break

        self.child_sources = tuple(child_sources)

    @override
    async def generate_pages(self):
        naming_scheme = self.volume.naming_scheme
        location = naming_scheme.make_location(self.path_in_volume, as_dir=True)

        # If we've already found a Source that will generate an index page, do nothing
        for child in self.child_sources:
            if isinstance(child, IndexSourceFile):
                self._set_index_page(child.page)
                self.pages = ()
                return

        # Otherwise, proceed to generate a simple index page
        title = self._data.get('title')
        meta = PageMeta(
            title=title,
            version=convert_or_none(Version.parse, self._data.get('version')))
        index_page = Page(self, location, Syntax.MD, meta, f'# {title}\n@toc')
        self._set_index_page(index_page)
        self.pages = index_page,

    @override
    def href(self, identifier: str = None) -> PageHref:
        from sobiraka.runtime import RT

        if identifier is not None:
            raise IdentifierResolutionError

        assert self.index_page is not None
        return PageHref(self.index_page, default_label=RT[self.index_page].title)

    # region Reading from YAML

    @cached_property
    def _data(self) -> dict:
        fs: FileSystem = self.volume.project.fs
        nav_path: RelativePath = self.path_in_project / NAV_FILENAME
        with fs.open_text(nav_path) as index_file:
            data = yaml.safe_load(index_file) or {}
            Draft202012Validator(data).validate(SCHEMA)

        return data

    @staticmethod
    def _parse_item(item) -> tuple[RelativePath, dict[str, Any]]:

        # - page.md
        if isinstance(item, str):
            return RelativePath(item), {}

        assert isinstance(item, dict)
        key, value = one(item.items())

        # - page.md: My Page
        if isinstance(value, str):
            return RelativePath(key), {'title': value}

        # - page.md: { ...meta... }
        if isinstance(value, dict):
            return RelativePath(key), value

        raise ValueError({key: value})

    # endregion
