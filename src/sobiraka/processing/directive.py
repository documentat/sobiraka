from abc import ABCMeta, abstractmethod
from argparse import ArgumentParser
from math import inf
from typing import Iterable

from panflute import Block, BulletList, Link, ListItem, Plain, Space, Str

from sobiraka.models import Page
from sobiraka.models.config import CombinedToc, Config
from sobiraka.processing.toc import Toc
from sobiraka.utils import Unnumbered, replace_element
from .abstract.processor import Processor


class Directive(Block, metaclass=ABCMeta):
    """
    Base class for a directive in documentation sources.

    A directive is a command that starts with the `@` symbol, has a name and optionally some arguments.
    It must be placed in what Pandoc considers a separate paragraph
    (the most sure way to do it is to add newlines before and after).

    During an early step of processing, the code in `Processor` walks through all paragraphs in the document.
    If a paragraph begins with one of the known directive names, it replaces the paragraph with a `Directive`.
    Later, when the code in `Dispatcher` finds this element, it calls its `run()` function.

    Directives are convenient for implementing features that need to put generated Pandoc AST elements into pages.
    For example, `TocDirective` is used a placeholder that is later replaced with other AST elements,
    all without the need to render the generated content into a temporary Markdown or other syntax.
    """

    def __init__(self, processor: Processor, page: Page):
        self.processor: Processor = processor
        self.page: Page = page

    def __repr__(self):
        return f'<{self.__class__.__name__} on {str(self.page.path_in_project)!r}>'

    @abstractmethod
    async def run(self) -> tuple[Block, ...]:
        ...


class TocDirective(Directive):

    def __init__(self, processor: Processor, page: Page, argv: list[str]):
        super().__init__(processor, page)

        parser = ArgumentParser(add_help=False)
        parser.add_argument('--combined', action='store_true')
        parser.add_argument('--depth', type=int, default=inf)
        parser.add_argument('--format', type=str, default='{}. ')

        args = parser.parse_args(argv)
        self.depth: int = args.depth
        self.combined: bool = args.combined
        self.format: str = args.format

    async def run(self) -> tuple[Block, ...]:
        """
        Do nothing at this stage, except remember the directive's position.
        The processor will iterate through `TocDirective`'s and call post-processing later.
        """
        self.processor.toc_placeholders[self.page].append(self)
        return self,

    def postprocess(self):
        """
        Replace the directive with a bullet list, based on a `toc()` call.
        """
        from sobiraka.processing.toc import toc

        toc = toc(self.page,
                  processor=self.processor,
                  current_page=self.page,
                  toc_depth=self.depth,
                  combined_toc=CombinedToc.ALWAYS if self.combined else CombinedToc.NEVER)
        bullet_list = BulletList(*self._make_items(toc))
        replace_element(self, bullet_list)

    def _make_items(self, toc: Toc) -> Iterable[ListItem]:
        config: Config = self.page.volume.config

        for item in toc:
            plain = Plain()
            if config.content.numeration and item.number is not Unnumbered:
                plain.content += Str(item.number.format(self.format)), Space()
            plain.content += Link(Str(item.title), url=item.url),

            li = ListItem(plain)

            if len(item.children) > 0:
                li.content.append(BulletList(*self._make_items(item.children)))

            yield li
