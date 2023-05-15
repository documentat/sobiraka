from dataclasses import dataclass
from textwrap import dedent
from typing import Awaitable, Callable

from sobiraka.models import Page


@dataclass
class TableOfContents:
    roots: list[Page]
    get_title: Callable[[Page], Awaitable[str]]

    async def _plaintext(self, line_template: str) -> str:
        text = ''
        for root in self.roots:
            for page in (root, *root.children_recursive):
                text += line_template.format(
                    indent="  " * page.level,
                    title=await self.get_title(page),
                    path=page.path_in_volume)
        text = dedent(text)
        return text

    @property
    async def rst(self) -> str:
        return await self._plaintext('{indent}- :doc:`{title} </{path}>`\n')

    @property
    async def md(self) -> str:
        return await self._plaintext('{indent}- [{title}](/{path})\n')
