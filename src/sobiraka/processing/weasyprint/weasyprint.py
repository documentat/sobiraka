from __future__ import annotations

import logging
import re
import sys
from asyncio import Task, create_task, to_thread
from contextlib import suppress
from functools import lru_cache
from mimetypes import guess_type
from typing import final

import weasyprint
from panflute import Doc, Element, Header, Image, Str
from typing_extensions import override

from sobiraka.models import FileSystem, Page, PageHref, PageStatus, Volume, RealFileSystem
from sobiraka.models.config import CombinedToc, Config, Config_Pygments
from sobiraka.models.exceptions import DisableLink
from sobiraka.processing import load_processor
from sobiraka.processing.abstract import Theme, ThemeableVolumeBuilder
from sobiraka.processing.web import AbstractHtmlBuilder, AbstractHtmlProcessor, HeadCssFile, Highlighter, Pygments
from sobiraka.report import update_progressbar
from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath, RelativePath, TocNumber, configured_jinja, convert_or_none


@final
class WeasyPrintBuilder(ThemeableVolumeBuilder['WeasyPrintProcessor', 'WeasyPrintTheme'], AbstractHtmlBuilder):

    def __init__(self, volume: Volume, output: AbsolutePath):
        ThemeableVolumeBuilder.__init__(self, volume)
        AbstractHtmlBuilder.__init__(self)

        self.output: AbsolutePath = output
        self.pseudofiles: dict[str, tuple[str, bytes]] = {}

    def init_processor(self) -> WeasyPrintProcessor:
        fs: FileSystem = self.get_project().fs
        config: Config = self.volume.config
        processor_class = load_processor(
            convert_or_none(fs.resolve, config.pdf.processor),
            config.pdf.theme,
            WeasyPrintProcessor)
        return processor_class(self)

    def init_theme(self) -> WeasyPrintTheme:
        return WeasyPrintTheme(self.volume.config.pdf.theme)

    @override
    def additional_variables(self) -> dict:
        return dict(PDF=True, HTML=True, WEASYPRINT=True)

    async def run(self):
        from ..toc import toc

        self.output.parent.mkdir(parents=True, exist_ok=True)

        volume: Volume = self.volume

        # Launch page processing tasks
        processing: dict[Page, Task] = {}
        for page in volume.pages:
            processing[page] = create_task(self.require(page, PageStatus.PROCESS4),
                                           name=f'generate html for {page.path_in_project}')

        # Launch non-page processing tasks
        self.add_html_task(self.add_custom_files())
        self.add_html_task(self.compile_theme_sass(self.theme, volume))

        # Combine rendered pages into a single page
        content: list[tuple[Page, TocNumber, str, str]] = []
        for page in volume.pages:
            await processing[page]
            content.append((page, RT[page].number, RT[page].title, RT[page].bytes.decode('utf-8')))

        await self.await_all_html_tasks()

        head = self.heads[volume].render('')

        # Apply the rendering template
        html = await self.theme.page_template.render_async(
            builder=self,

            project=volume.project,
            volume=volume,
            config=volume.config,

            head=head,
            toc=lambda **kwargs: toc(volume.root_page,
                                     builder=self,
                                     toc_depth=volume.config.pdf.toc_depth,
                                     combined_toc=CombinedToc.from_bool(volume.config.pdf.combined_toc),
                                     **kwargs),

            content=content,
        )

        update_progressbar('Writing PDF...')
        self.render_pdf(html)

    def render_pdf(self, html: str):
        messages = ''

        class WeasyPrintLogHandler(logging.NullHandler):
            def handle(self, record: logging.LogRecord):
                nonlocal messages
                messages += record.getMessage() + '\n'

        handler = WeasyPrintLogHandler()
        try:
            logging.getLogger('weasyprint').addHandler(handler)

            printer = weasyprint.HTML(string=html, base_url='sobiraka:print.html', url_fetcher=self.fetch_url)
            printer.write_pdf(self.output)

            if messages:
                raise WeasyPrintException(f'\n\n{messages}')

        finally:
            logging.getLogger('weasyprint').removeHandler(handler)

    def fetch_url(self, url: str) -> dict:
        config: Config = self.volume.config

        with suppress(KeyError):
            mime_type, content = self.pseudofiles[url]
            return dict(string=content, mime_type=mime_type)

        if re.match('^_static/(.+)$', url):
            file_path = self.theme.theme_dir / url
            mime_type, _ = guess_type(file_path, strict=False)
            return dict(file_obj=file_path.open('rb'), mime_type=mime_type)

        if ':' not in url:
            file_path = config.paths.resources / url
            mime_type, _ = guess_type(file_path, strict=False)[0]
            return dict(file_obj=file_path.open('rb'), mime_type=mime_type)

        print(url, file=sys.stderr)
        return weasyprint.default_url_fetcher(url)

    def make_internal_url(self, href: PageHref, *, page: Page = None) -> str:
        """
        Nobody really cares about how nice the internal URLs will in the intermediate HTML,
        so we use URLs like '#path/to/page.md' and '#path/to/page.md::section'.
        Luckily, WeasyPrint does not mind these characters.
        """
        if page is not None and page.volume is not href.target.volume:
            raise DisableLink
        result = '#' + str(href.target.path_in_volume)
        if href.anchor:
            result += '::' + href.anchor
        return result

    def get_root_prefix(self, page: Page) -> str:
        return ''

    @override
    def add_file_from_data(self, target: RelativePath, data: str | bytes):
        mime_type, _ = guess_type(target, strict=False)
        if isinstance(data, str):
            data = data.encode('utf-8')
        self.pseudofiles[str(target)] = mime_type, data

    @override
    async def add_file_from_location(self, source: AbsolutePath, target: RelativePath):
        raise NotImplementedError

    @override
    async def add_file_from_project(self, source: RelativePath, target: RelativePath):
        raise NotImplementedError

    @override
    def compile_sass(self, volume: Volume, source: AbsolutePath | bytes, target: RelativePath):
        self.pseudofiles[str(target)] = 'text/css', self.compile_sass_impl(source)
        self.heads[volume].append(HeadCssFile(target))

    def get_path_to_resources(self, page: Page) -> RelativePath:
        return RelativePath('_resources')

    def get_path_to_static(self, page: Page) -> RelativePath:
        return RelativePath('_static')  # TODO

    async def add_custom_files(self):
        config: Config = self.volume.config
        fs: FileSystem = self.volume.project.fs

        for style in config.pdf.custom_styles:
            source = RelativePath(style)
            match source.suffix:
                case '.css':
                    self.pseudofiles[f'css/{source.name}'] = 'text/css', fs.read_bytes(source)
                    self.heads[self.volume].append(HeadCssFile(RelativePath(f'css/{source.name}')))

                case '.sass' | '.scss':
                    # When building a real project, we rely on a RealFileSystem,
                    # so that SASS can include other files from the same directory.
                    # When in a test with a FakeFileSystem which cannot resolve(),
                    # we just read the source text and pipe it to SASS.
                    # Typically, tests do not use includes, so that's ok.
                    target = RelativePath('_static') / 'css' / f'{source.stem}.css'
                    if isinstance(fs, RealFileSystem):
                        self.add_html_task(to_thread(self.compile_sass, self.volume, fs.resolve(source), target))
                    else:
                        self.add_html_task(to_thread(self.compile_sass, self.volume, fs.read_bytes(source), target))

                case _:
                    raise ValueError(source)

    def get_relative_image_url(self, image: Image, page: Page) -> str:
        return image.url


class WeasyPrintProcessor(AbstractHtmlProcessor[WeasyPrintBuilder]):

    @override
    @lru_cache
    def get_highlighter(self, volume: Volume) -> Highlighter:
        config: Config = volume.config
        match config.pdf.highlight:
            case Config_Pygments() as config_pygments:
                return Pygments(config_pygments, self.builder)

    @override
    async def process_doc(self, doc: Doc, page: Page) -> None:
        try:
            assert len(doc.content) > 0
            header = doc.content[0]
            assert isinstance(header, Header)
            assert header.level == 1
        except AssertionError:
            doc.content.insert(0, Header(Str(page.stem), level=1))

        await super().process_doc(doc, page)

    @override
    async def process_header(self, header: Header, page: Page) -> tuple[Element, ...]:
        header, = await super().process_header(header, page)
        assert isinstance(header, Header)

        if header.level == 1:
            href = PageHref(page)
            header.identifier = self.builder.make_internal_url(href)[1:]
        else:
            anchor = RT[page].anchors.by_header(header)
            href = PageHref(page, anchor.identifier)
            header.identifier = self.builder.make_internal_url(href)[1:]

        if page.is_root():
            header.attributes['style'] = 'bookmark-level: none'
        else:
            header.attributes['style'] = f'bookmark-level: {page.level + header.level - 1}'

        self.builder.add_html_task(self.numerate_header(header, page))

        return header,

    async def numerate_header(self, header: Header, page: Page):
        await self.builder.require(page, PageStatus.PROCESS3)

        if header.level == 1:
            header.attributes['data-number'] = str(RT[page].number)
        else:
            anchor = RT[page].anchors.by_header(header)
            header.attributes['data-number'] = str(RT[anchor].number)


@final
class WeasyPrintTheme(Theme):
    def __init__(self, theme_dir: AbsolutePath):
        super().__init__(theme_dir)
        self.page_template = configured_jinja(theme_dir).get_template('print.html')


class WeasyPrintException(Exception):
    pass
