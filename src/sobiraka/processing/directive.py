from abc import ABCMeta, abstractmethod
from typing import Iterable

from panflute import Block, BulletList, Link, ListItem, Plain, Space, Str

from sobiraka.models import Page
from sobiraka.utils import UNNUMBERED
from .abstract.processor import Processor
from ..models.config import Config
from ..models.toc import Toc
from ..utils import replace_element


class Directive(Block, metaclass=ABCMeta):
    def __init__(self, processor: Processor, page: Page, _: list[str]):
        self.processor: Processor = processor
        self.page: Page = page

    def __repr__(self):
        return f'<{self.__class__.__name__} on {str(self.page.path_in_project)!r}>'

    @abstractmethod
    async def preprocess(self) -> tuple[Block, ...]:
        ...


class TocDirective(Directive):

    async def preprocess(self) -> tuple[Block, ...]:
        self.processor.toc_placeholders[self.page].append(self)
        return self,

    def postprocess(self):
        from sobiraka.models.toc import toc

        toc = toc(processor=self.processor, base=self.page, current_page=self.page)
        bullet_list = BulletList(*self._make_items(toc))
        replace_element(self, bullet_list)

    def _make_items(self, toc: Toc) -> Iterable[ListItem]:
        config: Config = self.page.volume.config

        for item in toc:
            plain = Plain()
            if config.content.numeration and item.number is not UNNUMBERED:
                plain.content += Str(str(item.number)), Space()
            plain.content += Link(Str(item.title), url=item.url),

            li = ListItem(plain)

            if len(item.children) > 0:
                li.content.append(BulletList(*self._make_items(item.children)))

            yield li
