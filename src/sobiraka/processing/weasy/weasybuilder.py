import logging
import re
import sys
from asyncio import Task, create_task
from mimetypes import guess_type
from types import NoneType

import weasyprint
from panflute import CodeBlock, Element, Header, Image, RawBlock

from sobiraka.models import Page, PageHref, PageStatus, Volume
from sobiraka.models.config import CombinedToc, Config
from sobiraka.models.exceptions import DisableLink
from sobiraka.processing.abstract import VolumeProcessor
from sobiraka.processing.plugin import WeasyTheme, load_weasy_theme
from sobiraka.processing.web.abstractwebbuilder import AbstractWebBuilder
from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath, RelativePath, TocNumber

logger = logging.getLogger('weasyprint')
logger.addHandler(logging.StreamHandler())


class WeasyBuilder(AbstractWebBuilder, VolumeProcessor):

    def __init__(self, volume: Volume, output: AbsolutePath):
        VolumeProcessor.__init__(self, volume)
        AbstractWebBuilder.__init__(self)

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
        content: list[tuple[Page, TocNumber, str, str]] = []
        for page in volume.pages:
            await processing[page]
            content.append((page, RT[page].number, RT[page].title, RT[page].bytes.decode('utf-8')))

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
        self.output.with_suffix('.html').write_text(html)

        printer = weasyprint.HTML(string=html,
                                  base_url='sobiraka:page.html',
                                  url_fetcher=self.fetch_url)
        printer.write_pdf(self.output)

    async def process4(self, page: Page):
        # Apply custom document processing
        if type(self.theme) not in (NoneType, WeasyTheme):
            await self.theme.process_doc(RT[page].doc, page)

        await super().process4(page)

    def fetch_url(self, url: str) -> dict:
        config: Config = self.volume.config

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

        if ':' not in url:
            file = config.paths.resources / url
            mime_type = guess_type(file, strict=False)[0]
            return dict(
                file_obj=open(file, 'rb'),
                mime_type=mime_type,
            )

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

    async def add_file_from_location(self, source: AbsolutePath, target: RelativePath):
        raise NotImplementedError

    async def add_file_from_project(self, source: RelativePath, target: RelativePath):
        raise NotImplementedError

    async def compile_sass(self, source: AbsolutePath, destination: RelativePath):
        raise NotImplementedError

    def get_path_to_resources(self, page: Page) -> RelativePath:
        return RelativePath('_resources')

    def get_path_to_static(self, page: Page) -> RelativePath:
        return RelativePath('_static')  # TODO

    def get_relative_image_url(self, image: Image, page: Page) -> str:
        return image.url

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

    async def process_header(self, header: Header, page: Page) -> tuple[Element, ...]:
        header, = await super().process_header(header, page)
        assert isinstance(header, Header)

        if header.level == 1:
            href = PageHref(page)
            header.identifier = self.make_internal_url(href)[1:]
        else:
            anchor = RT[page].anchors.by_header(header)
            href = PageHref(page, anchor.identifier)
            header.identifier = self.make_internal_url(href)[1:]

        return header,
