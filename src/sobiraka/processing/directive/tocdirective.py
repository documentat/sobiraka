from argparse import ArgumentParser
from dataclasses import dataclass
from math import inf
from typing import Iterable

from panflute import BulletList, Div, Element, Header, Link, ListItem, Plain, Str
from typing_extensions import override

from sobiraka.models.config import CombinedToc
from sobiraka.models.issues import Issue
from sobiraka.processing.toc import Toc, local_toc, toc
from .directive import Directive


class TocDirective(Directive):
    DIRECTIVE_NAME = '@toc'

    local: bool
    combined: bool

    depth: int
    format: str

    @classmethod
    @override
    def set_up_arguments(cls, parser: ArgumentParser):
        local_or_combined = parser.add_mutually_exclusive_group()
        local_or_combined.add_argument('--local', action='store_true')
        local_or_combined.add_argument('--combined', action='store_true')

        parser.add_argument('--depth', type=int, default=inf)
        parser.add_argument('--format', type=str, default='{}.')

    @override
    def postprocess(self):
        """
        Replace the directive with a bullet list, based on a `toc()` call.
        """
        if self.local:
            toc_items = local_toc(self.page,
                                  builder=self.builder,
                                  toc_depth=self.depth,
                                  current_page=self.page)
            header = self.previous_header()
            if header is not None and header.level != 1:
                parent_item = toc_items.find_item_by_header(header)
                toc_items = parent_item.children

        else:
            if self.combined:
                header = self.previous_header()
                if header is not None and header.level != 1:
                    self.page.issues.append(CombinedTocUnderSubheader())

            toc_items = toc(self.page,
                            builder=self.builder,
                            current_page=self.page,
                            toc_depth=self.depth,
                            combined_toc=CombinedToc.ALWAYS if self.combined else CombinedToc.NEVER)

        bullet_list = BulletList(*self.make_items(toc_items))
        return Div(bullet_list, classes=['toc'])

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

    def make_items(self, toc_items: Toc) -> Iterable[ListItem]:
        for item in toc_items:
            li = ListItem(Plain(Link(Str(item.title), url=item.url)))
            if len(item.children) > 0:
                li.content.append(BulletList(*self.make_items(item.children)))
            yield li


@dataclass(order=True, frozen=True)
class CombinedTocUnderSubheader(Issue):
    def __str__(self):
        return "Cannot use '@toc --combined' under a sub-header."
