from asyncio import gather
from pathlib import Path
from typing import Awaitable

from sobiraka.models import Page
from .abstract import Plainifier


class TxtBuilder(Plainifier):

    async def run(self, output: Path):
        tasks: list[Awaitable] = []
        for page in self.book.pages:
            txt_path = output / page.relative_path.with_suffix('.txt')
            tasks.append(self.render_page(page, txt_path))
        await gather(*tasks)

    async def render_page(self, page: Page, txt_path: Path):
        txt = await self.plainify(page)
        txt_path.parent.mkdir(parents=True, exist_ok=True)
        txt_path.write_text(txt)