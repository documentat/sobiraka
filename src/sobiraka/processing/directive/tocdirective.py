from argparse import ArgumentParser
from math import inf
from types import NoneType
from typing import Iterable, TYPE_CHECKING

from panflute import BulletList, Element, Header, Link, ListItem, Plain, Space, Str

from sobiraka.models import Page
from sobiraka.models.config import CombinedToc, Config
from sobiraka.utils import Unnumbered, replace_element
from .directive import Directive
from ..toc import Toc, local_toc, toc

if TYPE_CHECKING:
    from ..abstract import Processor


class TocDirective(Directive):
    def __init__(self, processor: 'Processor', page: Page, argv: list[str]):
        super().__init__(processor, page)

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
                        processor=self.processor,
                        current_page=self.page,
                        toc_depth=self.depth,
                        combined_toc=CombinedToc.ALWAYS if self.combined else CombinedToc.NEVER)
        bullet_list = BulletList(*_make_items(toc_items,
                                              format=self.format,
                                              numeration=config.content.numeration))
        replace_element(self, bullet_list)


class LocalTocDirective(Directive):
    def __init__(self, processor: 'Processor', page: Page, argv: list[str]):
        super().__init__(processor, page)

        parser = ArgumentParser(add_help=False)
        parser.add_argument('--depth', type=int, default=inf)
        parser.add_argument('--format', type=str, default='{}.')

        args = parser.parse_args(argv)
        self.depth: int = args.depth
        self.format: str = args.format

    def previous_header(self) -> Header | None:
        prev: Element | None = self.prev

        while True:
            match prev:
                case NoneType():
                    # Go one level up
                    prev = prev.parent.prev

                case Header():
                    # We found the closest previous header!
                    return prev

                case _:
                    # Continue looking, probably going one level up
                    if prev.prev is not None:
                        prev = prev.prev
                    elif prev.parent.prev is not None:
                        prev = prev.parent.prev
                    else:
                        return None

    def postprocess(self):
        """
        Replace the directive with a bullet list, based on a `local_toc()` call.
        """
        config: Config = self.page.volume.config

        toc_items = local_toc(self.page,
                              toc_depth=self.depth)

        header = self.previous_header()
        if header is not None:
            parent_item = toc_items.find_item_by_header(header)
            toc_items = parent_item.children

        bullet_list = BulletList(*_make_items(toc_items,
                                              format=self.format,
                                              numeration=config.content.numeration))
        replace_element(self, bullet_list)


def _make_items(toc_items: Toc, *, format: str, numeration: bool) -> Iterable[ListItem]:
    # pylint: disable=redefined-builtin

    for item in toc_items:
        plain = Plain(Link(Str(item.title), url=item.url))
        li = ListItem(plain)

        if numeration and item.number is not Unnumbered:
            plain.content = Str(item.number.format(format)), Space(), *plain.content

        if len(item.children) > 0:
            li.content.append(BulletList(*_make_items(item.children, format=format, numeration=numeration)))

        yield li
