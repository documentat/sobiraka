from __future__ import annotations

from abc import ABCMeta, abstractmethod
from asyncio import Task, TaskGroup, create_subprocess_exec, to_thread
from collections import defaultdict
from subprocess import PIPE, run
from typing import Generic, TypeVar, final

from panflute import CodeBlock, Element, Image
from typing_extensions import override

from sobiraka.models import Page, Volume
from sobiraka.models.config import Config
from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath, RelativePath, panflute_to_bytes
from .head import Head, HeadCssFile
from .highlight import Highlighter
from ..abstract import Builder, Processor, Theme


class AbstractHtmlBuilder(Builder, metaclass=ABCMeta):

    def __init__(self, **kwargs):
        Builder.__init__(self, **kwargs)

        self._html_builder_tasks: list[Task] = []
        self._results: set[AbsolutePath] = set()
        self.heads: dict[Volume, Head] = defaultdict(Head)

    @final
    async def compile_theme_sass(self, theme: Theme, volume: Volume):
        async with TaskGroup() as tg:
            theme_sass_dir = theme.theme_dir / 'sass'
            if theme_sass_dir.exists():
                for source in theme_sass_dir.iterdir():
                    if source.suffix in ('.sass', '.scss') and not source.stem.startswith('_'):
                        target = RelativePath('_static') / 'css' / f'{source.stem}.css'
                        tg.create_task(to_thread(self.compile_sass, volume, source, target))
                        self.heads[volume].append(HeadCssFile(target))

    @abstractmethod
    def compile_sass(self, volume: Volume, source: AbsolutePath | bytes, target: RelativePath):
        ...

    @final
    def compile_sass_impl(self, source: AbsolutePath | bytes) -> bytes:
        if isinstance(source, AbsolutePath):
            process = run(['sass', '--style=compressed', source.name], cwd=source.parent, stdout=PIPE, check=True)
        else:
            process = run(['sass', '--style=compressed', '--stdin'], input=source, stdout=PIPE, check=True)
        return process.stdout

    @override
    async def do_process4(self, page: Page):
        self.apply_postponed_image_changes(page)
        html = await self.render_html(page)
        RT[page].bytes = html

    @final
    def apply_postponed_image_changes(self, page: Page):
        for image, new_url in RT[page].converted_image_urls:
            image.url = new_url
        for image, link in RT[page].links_that_follow_images:
            link.url = image.url

    @final
    async def render_html(self, page: Page) -> bytes:
        pandoc = await create_subprocess_exec(
            'pandoc',
            '--from', 'json',
            '--to', 'html',
            '--wrap', 'none',
            '--no-highlight',
            stdin=PIPE,
            stdout=PIPE)
        html, _ = await pandoc.communicate(panflute_to_bytes(RT[page].doc))
        assert pandoc.returncode == 0

        return html

    @abstractmethod
    def get_root_prefix(self, page: Page) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_path_to_static(self, page: Page) -> RelativePath:
        raise NotImplementedError

    @abstractmethod
    def get_path_to_resources(self, page: Page) -> RelativePath:
        raise NotImplementedError

    @abstractmethod
    def get_relative_image_url(self, image: Image, page: Page) -> str:
        raise NotImplementedError

    ################################################################################
    # Functions used for additional tasks

    @abstractmethod
    def add_file_from_data(self, target: RelativePath, data: str | bytes):
        ...

    @abstractmethod
    async def add_file_from_location(self, source: AbsolutePath, target: RelativePath):
        raise NotImplementedError

    @final
    async def add_directory_from_location(self, source: AbsolutePath, target: RelativePath):
        async with TaskGroup() as tg:
            for file_source in source.walk_all():
                if file_source.is_file():
                    file_target = target / file_source.relative_to(source)
                    tg.create_task(self.add_file_from_location(file_source, file_target))

    @abstractmethod
    async def add_file_from_project(self, source: RelativePath, target: RelativePath):
        raise NotImplementedError


B = TypeVar('B', bound=AbstractHtmlBuilder)


class AbstractHtmlProcessor(Processor[B], Generic[B], metaclass=ABCMeta):

    @abstractmethod
    def get_highlighter(self, volume: Volume) -> Highlighter:
        """
        Load a Highlighter implementation based on the volume's configuration.
        The implementation and the possible result types differ for different builders.
        """

    @override
    async def process_code_block(self, block: CodeBlock, page: Page) -> tuple[Element, ...]:
        # Use the Highlighter implementation to process the code block and produce head tags
        highlighter = self.get_highlighter(page.volume)
        if highlighter is not None:
            block, head_tags = highlighter.highlight(block)
            self.builder.heads[page.volume] += head_tags
        return block,

    @override
    async def process_image(self, image: Image, page: Page) -> tuple[Image, ...]:
        config: Config = page.volume.config

        # Run the default processing
        # It is important to run it first, since it normalizes the path
        image, = await super().process_image(image, page)
        assert isinstance(image, Image)
        if image.url is None:
            return image,

        # Schedule copying the image file to the output directory
        source_path = config.paths.resources / image.url
        target_path = RelativePath(config.web.resources_prefix) / image.url
        self.builder.waiter.add_task(self.builder.add_file_from_project(source_path, target_path))

        # Use the path relative to the page path
        # (we postpone the actual change in the element to not confuse the WebTheme custom code later)
        new_url = self.builder.get_relative_image_url(image, page)
        if new_url != image.url:
            RT[page].converted_image_urls.append((image, new_url))

        return image,
