from __future__ import annotations

import logging
import re
import sys
import urllib.parse
from asyncio import Task, create_task
from mimetypes import guess_type
from types import NoneType
from typing import BinaryIO, NotRequired, TYPE_CHECKING, TypedDict

import jinja2
import weasyprint
from panflute import CodeBlock, Element, Image, RawBlock

from sobiraka.models import Page, PageHref, PageStatus, Volume
from sobiraka.models.config import CombinedToc
from sobiraka.models.exceptions import DisableLink
from sobiraka.processing.abstract import VolumeProcessor
from sobiraka.processing.html.abstracthtmlbuilder import AbstractHtmlBuilder
from sobiraka.processing.plugin import WeasyTheme, load_weasy_theme
from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath, RelativePath

logger = logging.getLogger('weasyprint')
logger.addHandler(logging.StreamHandler())


class WeasyBuilder(AbstractHtmlBuilder, VolumeProcessor):

    def __init__(self, volume: Volume, output: AbsolutePath):
        VolumeProcessor.__init__(self, volume)
        AbstractHtmlBuilder.__init__(self)

        self.output: AbsolutePath = output
        self.theme: WeasyTheme = load_weasy_theme(self.volume.config.weasyprint.theme)

        self.pseudofiles: dict[str, bytes] = {}

    async def run(self):
        from ..toc import toc

        self.output.parent.mkdir(parents=True, exist_ok=True)

        volume: Volume = self.volume

        # Launch page processing tasks
        processing: dict[Page, Task] = {}
        for page in volume.pages:
            processing[page] = create_task(self.require(page, PageStatus.PROCESS4),
                                           name=f'generate html for {page.path_in_project}')

        # Combine rendered pages into a single page
        content: list[tuple[Page, str, str]] = []
        for page in volume.pages:
            await processing[page]
            content.append((page, RT[page].title, RT[page].bytes.decode('utf-8')))

        # Apply the rendering template
        html = await self.theme.page_template.render_async(
            builder=self,

            project=volume.project,
            volume=volume,
            config=volume.config,

            toc=lambda **kwargs: toc(volume.root_page,
                                     processor=self,
                                     toc_depth=volume.config.weasyprint.toc_depth,
                                     combined_toc=CombinedToc.from_bool(volume.config.weasyprint.combined_toc),
                                     **kwargs),

            content=content,
        )

        self.pseudofiles['/page.html'] = html.encode('utf-8')

        printer = weasyprint.HTML(string=html,
                                  base_url='sobiraka:page.html',
                                  url_fetcher=self.fetch_url)
        printer.write_pdf(self.output)

    async def process4(self, page: Page):
        # Apply custom document processing
        if type(self.theme) not in (NoneType, WeasyTheme):
            await self.theme.process_doc(RT[page].doc, page)

        await super().process4(page)

    def fetch_url(self, url: str) -> FetchedString | FetchedFile:
        if url in self.pseudofiles:
            return dict(
                string=self.pseudofiles[url],
            )

        if m := re.match('^_static/(.+)$', url):
            file = self.theme.static_dir / m.group(1)
            mime_type = guess_type(file, strict=False)[0]
            return dict(
                file_obj=file.open('rb'),
                mime_type=mime_type,
            )

        print(url, file=sys.stderr)
        return weasyprint.default_url_fetcher(url)

    def make_internal_url(self, href: PageHref, *, page: Page) -> str:
        # TODO unduplicate
        if page is not None and page.volume is not href.target.volume:
            raise DisableLink
        result = href.target.id
        if href.anchor:
            result += '--' + href.anchor
        result = urllib.parse.quote(result).replace('%', '')
        result = '#' + result
        return result

    def get_root_prefix(self, page: Page) -> str:
        return ''

    async def add_file_from_location(self, source: AbsolutePath, target: RelativePath):
        raise NotImplementedError

    async def add_file_from_project(self, source: RelativePath, target: RelativePath):
        raise NotImplementedError

    async def compile_sass(self, source: AbsolutePath, destination: RelativePath):
        raise NotImplementedError

    def get_page_template(self, page: Page) -> jinja2.Template:
        raise NotImplementedError

    def get_path_to_resources(self, page: Page) -> RelativePath:
        return RelativePath('_resources')

    def get_path_to_static(self, page: Page) -> RelativePath:
        return RelativePath('_static')  # TODO

    def get_relative_image_url(self, image: Image, page: Page) -> str:
        raise NotImplementedError

    async def process_code_block(self, code: CodeBlock, page: Page) -> tuple[Element, ...]:
        from pygments.lexers import get_lexer_by_name
        from pygments.formatters.html import HtmlFormatter
        from pygments import highlight
        import yattag

        syntax, = code.classes or ('text',)
        pygments_lexer = get_lexer_by_name(syntax)
        pygments_formatter = HtmlFormatter(nowrap=True)
        pygments_output = highlight(code.text, pygments_lexer, pygments_formatter)

        html = yattag.Doc()
        with html.tag('div', klass=f'highlight-{syntax} notranslate'):
            with html.tag('div', klass='highlight'):
                with html.tag('pre'):
                    html.asis(pygments_output)

        return RawBlock(html.getvalue()),


if TYPE_CHECKING:
    class FetchedString(TypedDict):
        string: bytes
        mime_type: str
        encoding: NotRequired[str]
        redirected_url: NotRequired[str]
        filename: NotRequired[str]


    class FetchedFile(TypedDict):
        file_obj: BinaryIO
        mime_type: str
        encoding: NotRequired[str]
        redirected_url: NotRequired[str]
        filename: NotRequired[str]
