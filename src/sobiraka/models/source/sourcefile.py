import re

import yaml
from typing_extensions import override

from sobiraka.utils import MISSING
from .source import IdentifierResolutionError, Source
from ..href import PageHref
from ..namingscheme import NamingScheme
from ..page import Page, PageMeta
from ..syntax import Syntax

_META_PATTERN = re.compile(r'-{3,} \n (.+?\n)? -{3,} (?: \n+ (.+) )?', re.DOTALL | re.VERBOSE)


class SourceFile(Source):
    PAGE_CLASS = Page

    @override
    async def generate_pages(self):
        # Use the naming scheme to construct a clean location for the page
        naming_scheme: NamingScheme = self.volume.config.paths.naming_scheme
        location = naming_scheme.make_location(self.path_in_volume.with_suffix(''))

        # Choose syntax based on the file suffix
        try:
            syntax = Syntax(self.path_in_project.suffix[1:])
        except ValueError:
            syntax = Syntax.MD

        # Read raw text from the file
        text = self.volume.project.fs.read_text(self.path_in_project)

        # Parse the front matter, if any
        meta = self.base_meta or PageMeta()
        if m := _META_PATTERN.fullmatch(text):
            if meta_str := m.group(1):
                meta += PageMeta(**yaml.safe_load(meta_str))

        page = self.PAGE_CLASS(self, location, syntax, meta, text)
        page.children = []
        self.pages = page,

    @property
    def page(self) -> Page | None:
        assert self.pages is not MISSING, 'Too soon'
        return self.pages[0]

    @override
    def href(self, identifier: str = None) -> PageHref:
        from sobiraka.runtime import RT

        if identifier is None:
            return PageHref(self.page, default_label=self.page.meta.title)

        try:
            anchor = RT[self.page].anchors.by_identifier(identifier)
            return PageHref(self.page, identifier, default_label=anchor.label)

        except (KeyError, AssertionError) as exc:
            raise IdentifierResolutionError from exc
