from __future__ import annotations

from abc import ABCMeta, abstractmethod
from asyncio import Task, TaskGroup, create_subprocess_exec
from collections import defaultdict
from os.path import dirname
from subprocess import PIPE
from typing import Generic, TypeVar, final

from panflute import CodeBlock, Element, Header, Image
from typing_extensions import override

from sobiraka.models import Document, Page, Status
from sobiraka.models.config import Config, Config_Theme
from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath, RelativePath, configured_jinja, first_existing_path, panflute_to_bytes
from .head import Head, HeadCssFile
from .highlight import Highlighter
from ..abstract import Builder, Processor, Theme


class AbstractHtmlBuilder(Builder, metaclass=ABCMeta):

    def __init__(self, **kwargs):
        Builder.__init__(self, **kwargs)

        self._html_builder_tasks: list[Task] = []
        self._results: set[AbsolutePath] = set()
        self.heads: dict[Document, Head] = defaultdict(Head)

    @final
    async def compile_theme_sass(self, theme: AbstractHtmlTheme, document: Document, *, pdf: bool = False):
        """
        Generate CSS from up to three SASS/SCSS files:

        - the theme's main style,
        - the theme's flavor (if provided),
        - the project's customization (if provided).
        """
        if not theme.sass_main:
            return

        command = ['node', f'{dirname(__file__)}/compile_sass.js', '--source', str(theme.sass_main)]
        if pdf:
            command += '--pdf',
        if theme.sass_flavor:
            command += '--flavor', str(theme.sass_flavor)
        if theme.sass_customization:
            command += '--customization', str(document.project.fs.resolve(theme.sass_customization))

        process = await create_subprocess_exec(*command, stdout=PIPE)
        css, _ = await process.communicate()
        assert process.returncode == 0

        target = RelativePath() / '_static' / 'theme.css'
        self.add_file_from_data(target, css)
        self.heads[document].append(HeadCssFile(target))

    @final
    async def compile_sass(self, source: AbsolutePath | bytes) -> bytes:
        match source:
            case AbsolutePath() as source_path:
                process = await create_subprocess_exec('sass', '--style=compressed', source_path.name,
                                                       cwd=source_path.parent, stdout=PIPE)
                sass, _ = await process.communicate()
                assert process.returncode == 0
                return sass

            case bytes() as source_content:
                process = await create_subprocess_exec('sass', '--style=compressed', '--stdin', stdout=PIPE)
                sass, _ = await process.communicate(source_content)
                assert process.returncode
                return sass

            case _:
                raise ValueError(source)

    @override
    async def do_process4(self, page: Page):
        await super().do_process4(page)

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
    def get_highlighter(self, document: Document) -> Highlighter:
        """
        Load a Highlighter implementation based on the document's configuration.
        The implementation and the possible result types differ for different builders.
        """

    @override
    async def process_code_block(self, block: CodeBlock, page: Page) -> tuple[Element, ...]:
        # Use the Highlighter implementation to process the code block and produce head tags
        highlighter = self.get_highlighter(page.document)
        if highlighter is not None:
            block, head_tags = highlighter.highlight(block)
            self.builder.heads[page.document] += head_tags
        return block,

    @override
    async def process_header(self, header: Header, page: Page) -> tuple[Element, ...]:
        header, = await super().process_header(header, page)
        assert isinstance(header, Header)

        header.attributes['data-local-level'] = str(header.level)
        header.attributes['data-global-level'] = str(page.location.level + header.level - 1)

        self.builder.waiter.add_task(self.numerate_header(header, page))

        return header,

    @override
    async def process_image(self, image: Image, page: Page) -> tuple[Image, ...]:
        config: Config = page.document.config

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

    # -----------------------------------------------------------------------------------------------------------------

    async def numerate_header(self, header: Header, page: Page):
        await self.builder.waiter.wait(page, Status.PROCESS3)

        if header.attributes['data-local-level'] == '1':
            header.attributes['data-number'] = str(RT[page].number)
        else:
            anchor = RT[page].anchors.by_header(header)
            header.attributes['data-number'] = str(RT[anchor].number)


class AbstractHtmlTheme(Theme, metaclass=ABCMeta):
    TYPE: str

    def __init__(self, config: Config_Theme):
        super().__init__(config.path)
        self.page_template = configured_jinja(self.theme_dir).get_template(f'{self.TYPE}.html')
        self.sass_main = first_existing_path(
            self.theme_dir / 'sass' / f'{self.TYPE}.scss',
            self.theme_dir / 'sass' / f'{self.TYPE}.sass')
        self.sass_flavor = config.flavor and first_existing_path(
            self.theme_dir / 'sass' / '_flavors' / f'{config.flavor}.scss',
            self.theme_dir / 'sass' / '_flavors' / f'{config.flavor}.scss')
        self.sass_customization = config.customization

    def __repr__(self):
        return f'<{self.__class__.__name__}: {str(self.sass_main)!r}>'
