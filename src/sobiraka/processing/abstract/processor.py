import re
import sys
from asyncio import create_subprocess_exec, gather
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from subprocess import PIPE
from typing import Awaitable

import jinja2
import panflute
from panflute import Doc, Header, Image, Link, stringify

from sobiraka.models import Book, Href, Page, UrlHref
from sobiraka.models.error import BadLinkError, ProcessingError
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

        self.doc: dict[Page, Doc] = {}
        """The document tree, as parsed by `Pandoc <https://pandoc.org/>`_ and `Panflute <http://scorreia.com/software/panflute/>`_.
        
        Do not rely on the value for page here until :func:`load()` is awaited for that page."""

        self.titles: dict[Page, str | None] = {}
        """Page titles.
        
        Do not rely on the value for page here until :func:`process1()` is awaited for that page."""

        self.links: dict[Page, list[Href]] = defaultdict(list)
        """All links present on the page, both internal and external.-
        
        Do not rely on the value for page here until :func:`process1()` is awaited for that page."""

        self.anchors: dict[Page, dict[str, list[str]]] = defaultdict(dict)
        """Dictionary containing anchors and corresponding readable titles.
        
        Do not rely on the value for page here until :func:`process1()` is awaited for that page.
        
        Note that sometime a user leaves anchors empty or specifies identical anchors for multiple headers by mistake.
        However, this is not considered a critical error as long as no page contains links to this anchor.
        For that reason, all the titles for an anchor are stored as a list (in order of appearance on the page),
        and it is up to :func:`.process2_link()` to report an error if necessary.
        """

        self.errors: dict[Page, set[ProcessingError]] = defaultdict(set)

        self.process2_tasks: dict[Page, list[Awaitable]] = defaultdict(list)
        """:meta private:"""

    @on_demand
    async def load_page(self, page: Page):
        """
        Parse syntax tree with Pandoc and save its syntax tree into :obj:`.Page.doc`.

        This method is called by :obj:`.Page.loaded`.
        """
        from ...models.toc import TocGenerator

        variables = self.book.variables | {
            'toc': TocGenerator(page=page, processor=self),
        }

        page_text = page.raw()
        page_text = await self.jinja.from_string(page_text).render_async(variables)

        pandoc = await create_subprocess_exec(
            'pandoc',
            '--from', page.syntax,
            '--to', 'json',
            stdin=PIPE,
            stdout=PIPE)
        json_bytes, _ = await pandoc.communicate(page_text.encode('utf-8'))
        assert pandoc.returncode == 0

        self.doc[page] = panflute.load(BytesIO(json_bytes))
        save_debug_json('s0', page, self.doc[page])

    @on_demand
    async def process1(self, page: Page) -> Page:
        """
        Run first pass of page processing.

        Internally, this function runs :func:`process_element()` on the :obj:`.Page.doc` root.

        This method is called by :obj:`.Page.processed1`.
        """
        await self.load_page(page)
        await self.process_container(self.doc[page], page)
        self.titles.setdefault(page, page.path.stem)
        save_debug_json('s1', page, self.doc[page])
        return page

    async def process_header(self, elem: Header, page: Page):
        nodes = [elem]

        if not elem.identifier:
            elem.identifier = stringify(elem).lower().replace(' ', '-')

        self.anchors[page].setdefault(elem.identifier, []).append(stringify(elem))

        if elem.level == 1:
            full_id = page.id
        else:
            full_id = page.id + '--' + elem.identifier

        if elem.level == 1:
            self.titles[page] = stringify(elem)

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
                    self.errors[page].add(BadLinkError(target))

        self.links[page].append(href)
        if isinstance(href, PageHref):
            self.process2_tasks[page].append(self.process2_link(page, elem, href))

    @on_demand
    async def process2(self, page: Page):
        await self.process1(page)
        await gather(*self.process2_tasks[page])
        save_debug_json('s2', page, self.doc[page])

    async def process2_link(self, page: Page, elem: Link, href: PageHref):
        await self.process1(href.target)

        elem.url = '#' + href.target.id
        elem.title = self.titles[href.target]

        if href.anchor:
            try:
                elem.url += '--' + href.anchor
                elem.title = self.anchors[href.target][href.anchor]
            except KeyError:
                self.errors[page].add(BadLinkError(f'{href.target.relative_path}#{href.anchor}'))

    def print_errors(self) -> bool:
        errors_found: bool = False
        for page in self.book.pages:
            if self.errors[page]:
                message = f'Errors in {page.relative_path}:'
                errors = sorted(self.errors[page], key=lambda e: (e.__class__.__name__, e))
                for error in errors:
                    message += f'\n    {error}'
                message += '\n'
                print(message, file=sys.stderr)
                errors_found = True
        return errors_found