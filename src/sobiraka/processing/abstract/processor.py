import re
import sys
from abc import abstractmethod
from asyncio import create_subprocess_exec, gather
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from subprocess import PIPE
from typing import Awaitable

import jinja2
import panflute
from more_itertools import padded
from panflute import Code, Doc, Element, Header, Link, Str, stringify

from sobiraka.models import Anchor, Anchors, BadLink, DirPage, Href, Issue, Page, PageHref, Project, UrlHref, Volume
from sobiraka.utils import LatexBlock, UniqueList, on_demand, save_debug_json
from .dispatcher import Dispatcher


class Processor(Dispatcher):
    def __init__(self):
        self.jinja = jinja2.Environment(
            comment_start_string='{{#',
            comment_end_string='#}}',
            enable_async=True)

        self.doc: dict[Page, Doc] = {}
        """
        The document tree, as parsed by `Pandoc <https://pandoc.org/>`_ 
        and `Panflute <http://scorreia.com/software/panflute/>`_.
        
        Do not rely on the value for page here until :func:`load()` is awaited for that page.
        """

        self.titles: dict[Page, str | None] = {}
        """Page titles.
        
        Do not rely on the value for page here until :func:`process1()` is awaited for that page."""

        self.links: dict[Page, list[Href]] = defaultdict(list)
        """All links present on the page, both internal and external.-
        
        Do not rely on the value for page here until :func:`process1()` is awaited for that page."""

        self.anchors: dict[Page, Anchors] = defaultdict(Anchors)
        """Dictionary containing anchors and corresponding readable titles.
        
        Do not rely on the value for page here until :func:`process1()` is awaited for that page.
        
        Note that sometime a user leaves anchors empty or specifies identical anchors for multiple headers by mistake.
        However, this is not considered a critical issue as long as no page contains links to this anchor.
        For that reason, all the titles for an anchor are stored as a list (in order of appearance on the page),
        and it is up to :func:`.process2_link()` to report an issue if necessary.
        """

        self.issues: dict[Page, UniqueList[Issue]] = defaultdict(UniqueList)

        self.process2_tasks: dict[Page, list[Awaitable]] = defaultdict(list)
        """:meta private:"""

    @abstractmethod
    def get_pages(self) -> tuple[Page, ...]:
        ...

    @on_demand
    async def load_page(self, page: Page):
        """
        Parse syntax tree with Pandoc and save its syntax tree into :obj:`.Page.doc`.

        This method is called by :obj:`.Page.loaded`.
        """
        from sobiraka.models import SubtreeToc

        variables = page.volume.variables | {
            'toc': SubtreeToc(self, page),
            'LANG': page.volume.lang,
        }

        page_text = page.text()
        page_text = await self.jinja.from_string(page_text).render_async(variables)

        pandoc = await create_subprocess_exec(
            'pandoc',
            '--from', page.syntax.as_pandoc_format(),
            '--to', 'json',
            stdin=PIPE,
            stdout=PIPE)
        json_bytes, _ = await pandoc.communicate(page_text.encode('utf-8'))
        assert pandoc.returncode == 0

        self.doc[page] = panflute.load(BytesIO(json_bytes))
        save_debug_json('s0', page, self.doc[page])

    async def get_title(self, page: Page) -> str:
        # TODO: maybe make get_title() a separate @on_demand step?
        await self.process1(page)
        if page not in self.titles:
            self.titles[page] = page.id_segment()
        return self.titles[page]

    @on_demand
    async def process1(self, page: Page) -> Page:
        """
        Run first pass of page processing.

        Internally, this function runs :func:`process_element()` on the :obj:`.Page.doc` root.

        This method is called by :obj:`.Page.processed1`.
        """
        await self.load_page(page)
        await self.process_container(self.doc[page], page)
        save_debug_json('s1', page, self.doc[page])
        return page

    async def process_header(self, elem: Header, page: Page) -> tuple[Element, ...]:
        nodes = [elem]

        if not elem.identifier:
            elem.identifier = stringify(elem).lower().replace(' ', '-')

        anchor = Anchor(elem.identifier, stringify(elem), elem)
        self.anchors[page].append(anchor)

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

    def print_issues(self) -> bool:
        issues_found: bool = False
        for page in self.get_pages():
            if self.issues[page]:
                message = f'Issues in {page.path_in_project}:'
                for issue in self.issues[page]:
                    message += f'\n    {issue}'
                message += '\n'
                print(message, file=sys.stderr)
                issues_found = True
        return issues_found

    # --------------------------------------------------------------------------------
    # Internal links

    async def process_link(self, elem: Link, page: Page):
        if re.match(r'^\w+:', elem.url):
            self.links[page].append(UrlHref(elem.url))
        else:
            if page.path.suffix == '.rst':
                self.issues[page].append(BadLink(elem.url))
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
        return (link,)

    async def _process_internal_link(self, elem: Link, target_text: str, page: Page):
        target_path_str, target_anchor = padded(target_text.split('#', maxsplit=1), None, 2)
        if target_path_str:
            try:
                if target_path_str.startswith('/'):
                    target_path = page.volume.relative_root / Path(target_path_str[1:])
                else:
                    if isinstance(page, DirPage):
                        target_path = (page.path / target_path_str).resolve()
                    else:
                        target_path = (page.path.parent / target_path_str).resolve()
                    target_path = target_path.relative_to(page.volume.project.base)
                target = page.volume.pages_by_path[target_path]
            except (KeyError, ValueError):
                self.issues[page].append(BadLink(target_text))
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
        elem.url = self.make_internal_url(href, page=page)

        if href.anchor:
            try:
                autolabel = self.anchors[href.target][href.anchor].label
            except (KeyError, AssertionError):
                self.issues[page].append(BadLink(target_text))
                return
        else:
            autolabel = await self.get_title(href.target)

        if not elem.content:
            elem.content = Str(autolabel)

    @abstractmethod
    def make_internal_url(self, href: PageHref, *, page: Page) -> str:
        ...


class ProjectProcessor(Processor):
    # TODO: add ABCMeta to the base Processor class
    # pylint: disable=abstract-method
    def __init__(self, project: Project):
        super().__init__()
        self.project: Project = project

    def get_pages(self) -> tuple[Page, ...]:
        return self.project.pages


class VolumeProcessor(Processor):
    # pylint: disable=abstract-method
    def __init__(self, volume: Volume):
        super().__init__()
        self.volume: Volume = volume

    def get_pages(self) -> tuple[Page, ...]:
        return self.volume.pages
