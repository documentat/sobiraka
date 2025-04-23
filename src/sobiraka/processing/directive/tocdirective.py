from argparse import ArgumentParser
from math import inf
from typing import Iterable

from panflute import BulletList, Div, Element, Header, Link, ListItem, Plain, Str
from typing_extensions import override

from sobiraka.models.config import CombinedToc, Config
from sobiraka.processing.toc import Toc, local_toc, toc
from .directive import Directive


class TocDirective(Directive):
    DIRECTIVE_NAME = '@toc'

    depth: int
    combined: bool
    format: str

    @classmethod
    @override
    def set_up_arguments(cls, parser: ArgumentParser):
        parser.add_argument('--depth', type=int, default=inf)
        parser.add_argument('--combined', action='store_true')
        parser.add_argument('--format', type=str, default='{}.')

    @override
    def postprocess(self):
        """
        Replace the directive with a bullet list, based on a `toc()` call.
        """
        config: Config = self.page.volume.config

        toc_items = toc(self.page,
                        builder=self.builder,
                        current_page=self.page,
                        toc_depth=self.depth,
                        combined_toc=CombinedToc.ALWAYS if self.combined else CombinedToc.NEVER)
        bullet_list = BulletList(*_make_items(toc_items,
                                              format=self.format,
                                              numeration=config.content.numeration))
        return Div(bullet_list, classes=['toc'])


class LocalTocDirective(Directive):
    DIRECTIVE_NAME = '@local-toc'

    depth: int
    format: str

    @classmethod
    @override
    def set_up_arguments(cls, parser: ArgumentParser):
        parser.add_argument('--depth', type=int, default=inf)
        parser.add_argument('--format', type=str, default='{}.')

    def previous_header(self) -> Header | None:
        elem: Element | None = self

        while True:
            # Go one step back and, if necessary, one level up
            if elem.prev is not None:
                elem = elem.prev
            elif elem.parent.prev is not None:
                elem = elem.parent.prev
            else:
                return None

            # Check if the element is a header
            if isinstance(elem, Header):
                return elem

    @override
    def postprocess(self):
        """
        Replace the directive with a bullet list, based on a `local_toc()` call.
        """
        config: Config = self.page.volume.config

        toc_items = local_toc(self.page,
                              builder=self.builder,
                              toc_depth=self.depth,
                              current_page=self.page)

        header = self.previous_header()
        if header is not None and header.level != 1:
            parent_item = toc_items.find_item_by_header(header)
            toc_items = parent_item.children

        bullet_list = BulletList(*_make_items(toc_items,
                                              format=self.format,
                                              numeration=config.content.numeration))
        return Div(bullet_list, classes=['toc'])


def _make_items(toc_items: Toc, *, format: str, numeration: bool) -> Iterable[ListItem]:
    # pylint: disable=redefined-builtin
    for item in toc_items:
        li = ListItem(Plain(Link(Str(item.title), url=item.url)))
        if len(item.children) > 0:
            li.content.append(BulletList(*_make_items(item.children, format=format, numeration=numeration)))
        yield li
