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
from more_itertools import padded
from panflute import Code, Doc, Header, Image, Link, Str, stringify

from sobiraka.models import Book, Href, Page, UrlHref
from sobiraka.models.error import BadLinkError, ProcessingError
from sobiraka.models.href import PageHref
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
        from sobiraka.utils.toc import TocGenerator

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

    @on_demand
    async def process2(self, page: Page):
        await self.process1(page)
        await gather(*self.process2_tasks[page])
        save_debug_json('s2', page, self.doc[page])

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

    # --------------------------------------------------------------------------------
    # Internal links

    async def process_link(self, elem: Link, page: Page):
        if re.match(r'^\w+:', elem.url):
            self.links[page].append(UrlHref(elem.url))
        else:
            if page.path.suffix == '.rst':
                self.errors[page].add(BadLinkError(elem.url))
                return
            await self._process_internal_link(elem, elem.url, page)

    async def process_role_doc(self, elem: Code, page: Page):
        if m := re.fullmatch(r'(.+) < (.+) >', elem.text, flags=re.X):
            label = m.group(1).strip()
            target_text = m.group(2)
        else:
            label = None
            target_text = elem.text

        link = Link(Str(label))
        await self._process_internal_link(link, target_text, page)
        return link,

    async def _process_internal_link(self, elem: Link, target_text: str, page: Page):
        target_path_str, target_anchor = padded(target_text.split('#', maxsplit=1), None, 2)
        if target_path_str:
            try:
                if target_path_str.startswith('/'):
                    target_path = Path(target_path_str[1:])
                else:
                    target_path = (page.path.parent / target_path_str).resolve().relative_to(self.book.root)
                target = self.book.pages_by_path[target_path]
            except (KeyError, ValueError):
                self.errors[page].add(BadLinkError(target_text))
                return
        else:
            target = page

        href = PageHref(target, target_anchor)
        self.links[page].append(href)

        self.process2_tasks[page].append(self.process2_internal_link(elem,
                                                                     href=href,
                                                                     target_text=target_text,
                                                                     page=page))

    async def process2_internal_link(self, elem: Link, *, href: PageHref, target_text: str, page: Page):
        await self.process1(href.target)

        if href.anchor:
            try:
                assert len(self.anchors[href.target][href.anchor]) == 1
                elem.url = f'#{href.target.id}--{href.anchor}'
                autolabel = self.anchors[href.target][href.anchor]
            except (KeyError, AssertionError):
                self.errors[page].add(BadLinkError(target_text))
                return
        else:
            elem.url = f'#{href.target.id}'
            autolabel = self.titles[href.target]

        if not elem.content:
            elem.content = Str(autolabel)