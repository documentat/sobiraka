from asyncio import create_task, sleep
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import IsolatedAsyncioTestCase, main

from sobiraka.models import Page
from sobiraka.models.load import load_project
from sobiraka.processing import PdfBuilder


class TestPageProcessingOrder(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        temp_dir: str = self.enterContext(TemporaryDirectory(prefix='sobiraka-test-'))
        self.dir: Path = Path(temp_dir)

        manifest_path = self.dir / 'project.yaml'
        manifest_path.touch()
        self.project = load_project(manifest_path)

        page_path = self.dir / 'page.md'
        page_path.touch()
        self.page = Page(self.project.volumes[0], self.dir / 'page.md')

        self.processor = PdfBuilder(self.project.volumes[0], self.dir / 'page.pdf')  # TODO make a simpler processor

        self.order: list[str] = []

    async def test_order(self):
        create_task(self.wait_until_loaded(self.page))
        create_task(self.wait_until_processed1(self.page))
        create_task(self.wait_until_processed2(self.page))

        await self.processor.process2(self.page)
        await sleep(0)

        expected_order = 'loaded', 'processed1', 'processed2'
        self.assertSequenceEqual(expected_order, self.order)

    async def wait_until_loaded(self, page: Page):
        await self.processor.load_page(page)
        self.order.append('loaded')

    async def wait_until_processed1(self, page: Page):
        await self.processor.process1(page)
        self.order.append('processed1')

    async def wait_until_processed2(self, page: Page):
        await self.processor.process2(page)
        self.order.append('processed2')


if __name__ == '__main__':
    main()
