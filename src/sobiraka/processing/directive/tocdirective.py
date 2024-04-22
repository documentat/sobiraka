from argparse import ArgumentParser
from math import inf
from typing import Iterable, TYPE_CHECKING

from panflute import BulletList, Link, ListItem, Plain, Space, Str

from sobiraka.models import Page
from sobiraka.models.config import CombinedToc, Config
from sobiraka.utils import Unnumbered, replace_element
from .directive import Directive
from ..toc import Toc, toc

if TYPE_CHECKING:
    from ..abstract import Processor


class TocDirective(Directive):

    def __init__(self, processor: 'Processor', page: Page, argv: list[str]):
        super().__init__(processor, page)

        parser = ArgumentParser(add_help=False)
        parser.add_argument('--combined', action='store_true')
        parser.add_argument('--depth', type=int, default=inf)
        parser.add_argument('--format', type=str, default='{}.')

        args = parser.parse_args(argv)
        self.depth: int = args.depth
        self.combined: bool = args.combined
        self.format: str = args.format

    def postprocess(self):
        """
        Replace the directive with a bullet list, based on a `toc()` call.
        """
        toc_items = toc(self.page,
                        processor=self.processor,
                        current_page=self.page,
                        toc_depth=self.depth,
                        combined_toc=CombinedToc.ALWAYS if self.combined else CombinedToc.NEVER)
        bullet_list = BulletList(*self._make_items(toc_items))
        replace_element(self, bullet_list)

    def _make_items(self, toc_items: Toc) -> Iterable[ListItem]:
        config: Config = self.page.volume.config

        for item in toc_items:
            plain = Plain()
            if config.content.numeration and item.number is not Unnumbered:
                plain.content += Str(item.number.format(self.format)), Space()
            plain.content += Link(Str(item.title), url=item.url),

            li = ListItem(plain)

            if len(item.children) > 0:
                li.content.append(BulletList(*self._make_items(item.children)))

            yield li
