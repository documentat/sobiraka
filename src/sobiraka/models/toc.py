from __future__ import annotations

from dataclasses import dataclass, replace
from textwrap import dedent

from sobiraka.models import Page
from sobiraka.processing.abstract import Processor


@dataclass(kw_only=True)
class TocGenerator:
    page: Page
    processor: Processor

    _is_local: bool = False

    @property
    def local(self) -> TocGenerator:
        return replace(self, _is_local=True)

    async def rst(self) -> str:
        pages = self.page.children_recursive if self._is_local else self.processor.book.pages

        text = ''
        for page in pages:
            if page is not self.page:
                await self.processor.process1(page)
            prefix = '  ' * page.level
            text += f'{prefix}- {page.title}: {page.relative_path}\n'

        text = dedent(text)
        return text