from argparse import ArgumentParser
from math import inf
from typing import Iterable, TYPE_CHECKING

from panflute import BulletList, Div, Element, Header, Link, ListItem, Plain, Str

from sobiraka.models import Page
from sobiraka.models.config import CombinedToc, Config
from sobiraka.utils import replace_element
from .directive import Directive
from ..toc import Toc, local_toc, toc

if TYPE_CHECKING:
    from ..abstract import Builder


class TocDirective(Directive):
    def __init__(self, builder: 'Builder', page: Page, argv: list[str]):
        super().__init__(builder, page)

        parser = ArgumentParser(add_help=False)
        parser.add_argument('--depth', type=int, default=inf)
        parser.add_argument('--combined', action='store_true')
        parser.add_argument('--format', type=str, default='{}.')

        args = parser.parse_args(argv)
        self.depth: int = args.depth
        self.combined: bool = args.combined
        self.format: str = args.format

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
        div = Div(bullet_list, classes=['toc'])
        replace_element(self, div)


class LocalTocDirective(Directive):
    def __init__(self, builder: 'Builder', page: Page, argv: list[str]):
        super().__init__(builder, page)

        parser = ArgumentParser(add_help=False)
        parser.add_argument('--depth', type=int, default=inf)
        parser.add_argument('--format', type=str, default='{}.')

        args = parser.parse_args(argv)
        self.depth: int = args.depth
        self.format: str = args.format

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
        div = Div(bullet_list, classes=['toc'])
        replace_element(self, div)


def _make_items(toc_items: Toc, *, format: str, numeration: bool) -> Iterable[ListItem]:
    # pylint: disable=redefined-builtin
    for item in toc_items:
        li = ListItem(Plain(Link(Str(item.title), url=item.url)))
        if len(item.children) > 0:
            li.content.append(BulletList(*_make_items(item.children, format=format, numeration=numeration)))
        yield li
