import re
from asyncio import create_subprocess_exec, gather
from io import BytesIO
from pathlib import Path
from subprocess import PIPE

import jinja2
import panflute
from panflute import Header, Image, Link, stringify

from sobiraka.models import Book, Href, Page, UrlHref
from sobiraka.models.error import BadLinkError
from sobiraka.models.href import PageHref, UnknownPageHref
from sobiraka.utils import LatexBlock, on_demand, save_debug_json
from .dispatcher import Dispatcher


class Processor(Dispatcher):

    def __init__(self, book: Book):
        self.book: Book = book

        self.jinja = jinja2.Environment(
            comment_start_string='{{#',
            comment_end_string='#}}',
            enable_async=True)

    def get_syntax(self, suffix: str) -> str:
        match suffix:
            case '.md':
                return 'markdown'
            case '.rst':
                return 'rst-auto_identifiers'
            case _:  # pragma: no cover
                raise NotImplementedError(suffix)

    @on_demand
    async def load_page(self, page: Page):
        """
        Parse syntax tree with Pandoc and save its syntax tree into :obj:`.Page.doc`.

        This method is called by :obj:`.Page.loaded`.
        """
        from ...models.toc import TocGenerator

        page_text = page.path.read_text('utf-8')
        variables = self.book.variables | {
            'toc': TocGenerator(page=page, processor=self),
        }
        page_text = await self.jinja.from_string(page_text).render_async(variables)

        pandoc = await create_subprocess_exec(
            'pandoc',
            '--from', self.get_syntax(page.path.suffix),
            '--to', 'json',
            stdin=PIPE,
            stdout=PIPE)
        json_bytes, _ = await pandoc.communicate(page_text.encode('utf-8'))
        assert pandoc.returncode == 0

        page.doc = panflute.load(BytesIO(json_bytes))
        save_debug_json('s0', page)

    @on_demand
    async def process1(self, page: Page) -> Page:
        """
        Run first pass of page processing.

        Internally, this function runs :func:`process_element()` on the :obj:`.Page.doc` root.

        This method is called by :obj:`.Page.processed1`.
        """
        await self.load_page(page)
        await self.process_container(page.doc, page)
        save_debug_json('s1', page)
        return page

    async def process_header(self, elem: Header, page: Page):
        nodes = [elem]

        if not elem.identifier:
            elem.identifier = stringify(elem).lower().replace(' ', '-')

        page.anchors.setdefault(elem.identifier, []).append(stringify(elem))

        if elem.level == 1:
            full_id = page.id
        else:
            full_id = page.id + '--' + elem.identifier

        if elem.level == 1 and page.title is None:
            page.title = stringify(elem)

        nodes.insert(0, LatexBlock(fr'''
            \hypertarget{{{full_id}}}{{}}
            \bookmark[level={page.level},dest={full_id}]{{{stringify(elem)}}}
        '''))

        if page.antilevel > 1:
            nodes.insert(0, LatexBlock(r'\newpage'))
            nodes.append(LatexBlock(r'\newpage'))

        return tuple(nodes)

    async def process_image(self, elem: Image, page: Page):
        elem.url = str(self.book.root / '_images' / elem.url)

    async def process_link(self, elem: Link, page: Page):
        href: Href

        if re.match(r'^\w+:', elem.url):
            href = UrlHref(elem.url)

        else:
            m = re.match(r'^ ([^\#]+)? (?: \#(.+) )?', elem.url, flags=re.VERBOSE)
            target, anchor = m.groups()
            target = target or None
            anchor = anchor or None

            if target is None:
                href = PageHref(page, anchor)
            else:
                try:
                    target_path = (page.path.parent / Path(target)).resolve().relative_to(self.book.root)
                    target_page = self.book.pages_by_path[target_path]
                    href = PageHref(target_page, anchor)
                except (KeyError, ValueError):
                    href = UnknownPageHref(target, anchor)
                    page.errors.add(BadLinkError(target))

        page.links.append(href)
        if isinstance(href, PageHref):
            page.process2_tasks.append(self.process2_link(page, elem, href))

    @on_demand
    async def process2(self, page: Page):
        await self.process1(page)
        await gather(*page.process2_tasks)
        save_debug_json('s2', page)

    async def process2_link(self, page: Page, elem: Link, href: PageHref):
        await self.process1(href.target)

        elem.url = '#' + href.target.id
        elem.title = href.target.title

        if href.anchor:
            try:
                elem.url += '--' + href.anchor
                elem.title = href.target.anchors[href.anchor]
            except KeyError:
                page.errors.add(BadLinkError(f'{href.target.relative_path}#{href.anchor}'))