from __future__ import annotations

from dataclasses import dataclass, replace
from textwrap import dedent
from typing import Callable

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

    async def _plaintext(self, make_line: Callable[[Page], str]) -> str:
        pages = self.page.children_recursive if self._is_local else self.page.volume.project.pages
        text = ''
        for page in pages:
            if page is not self.page:
                await self.processor.process1(page)
            text += make_line(page)
        text = dedent(text)
        return text

    async def rst(self) -> str:
        return await self._plaintext(lambda page: f'{"  " * page.level}- :doc:`{self.processor.titles[page]} </{page.path_in_volume}>`\n')

    async def md(self) -> str:
        return await self._plaintext(lambda page: f'{"  " * page.level}- [{self.processor.titles[page]}](/{page.path_in_volume})\n')