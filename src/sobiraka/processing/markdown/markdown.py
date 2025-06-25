from __future__ import annotations

from asyncio import create_subprocess_exec, create_task, to_thread
from subprocess import PIPE
from typing import final

from panflute import Element, Header, Image
from typing_extensions import override

from sobiraka.models import Page, PageHref, Volume
from sobiraka.models.config import Config
from sobiraka.processing.abstract import Processor, VolumeBuilder
from sobiraka.processing.abstract.processor import DisableLink
from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath, RelativePath, delete_extra_files, panflute_to_bytes


@final
class MarkdownBuilder(VolumeBuilder['MarkdownProcessor']):
    """
    A special buider for exporting the documentation to a Pandoc-compatible single-file markdown document.
    The images are saved next to the document, too.
    """

    def __init__(self, volume: Volume, output: AbsolutePath):
        super().__init__(volume)
        self.output: AbsolutePath = output
        self._results: set[AbsolutePath] = set()

    @override
    def init_processor(self) -> MarkdownProcessor:
        return MarkdownProcessor(self)

    @override
    async def run(self):
        self.output.mkdir(parents=True, exist_ok=True)

        volume = self.volume

        # Process all pages
        await self.waiter.wait_all()

        # Combine results into a single document
        markdown_path = self.output / f'{self.output.name}.md'
        self._results.add(markdown_path)
        with markdown_path.open('w') as markdown:
            markdown.write(f'---\ntitle: {volume.config.title}\n---')
            for page in volume.root.all_pages():
                markdown.write('\n\n' + RT[page].bytes.decode('utf-8'))

        delete_extra_files(self.output, self._results)

    @override
    async def do_process4(self, page: Page):
        await super().do_process4(page)

        if len(RT[page].doc.content) == 0:
            RT[page].bytes = b''

        else:
            pandoc = await create_subprocess_exec(
                'pandoc',
                # '--shift-heading-level-by', '1',
                '--from', 'json',
                '--to', 'markdown-multiline_tables',
                '--wrap', 'none',
                stdin=PIPE,
                stdout=PIPE)
            pandoc.stdin.write(panflute_to_bytes(RT[page].doc))
            pandoc.stdin.close()
            await pandoc.wait()
            assert pandoc.returncode == 0
            RT[page].bytes = await pandoc.stdout.read()

    @override
    def additional_variables(self) -> dict:
        return dict()

    @override
    def make_internal_url(self, href: PageHref, *, page: Page = None) -> str:
        # Same implementation as in WeasyPrintBuilder,
        # but slashes are replaced with double dashes
        if page is not None and page.volume is not href.target.volume:
            raise DisableLink
        result = '#' + str(href.target.location)
        result = result.replace('/', '--')
        if href.anchor:
            result += '::' + href.anchor
        return result

    async def add_file_from_project(self, source: RelativePath, target: RelativePath):
        target = self.output / target
        await to_thread(self.volume.project.fs.copy, source, target)
        self._results.add(target)


@final
class MarkdownProcessor(Processor[MarkdownBuilder]):

    @override
    async def process_header(self, header: Header, page: Page) -> tuple[Element, ...]:
        header, = await super().process_header(header, page)
        assert isinstance(header, Header)

        if header.level == 1:
            header.identifier = self.builder.make_internal_url(PageHref(page))[1:]
        else:
            anchor = RT[page].anchors.by_header(header)
            header.identifier = self.builder.make_internal_url(PageHref(page, anchor.identifier))[1:]

        return header,

    @override
    async def process_image(self, image: Image, page: Page) -> tuple[Image, ...]:
        config: Config = page.volume.config

        # Run the default processing
        image, = await super().process_image(image, page)
        assert isinstance(image, Image)
        if image.url is None:
            return image,

        # Schedule copying the image file to the output directory
        source_path = config.paths.resources / image.url
        target_path = RelativePath('resources') / image.url
        self.builder.process2_tasks[page].append(create_task(
            self.builder.add_file_from_project(source_path, target_path)))

        image.url = str(target_path)

        return image,
