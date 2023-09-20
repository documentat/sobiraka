import re
import sys
from abc import abstractmethod
from asyncio import Task, create_subprocess_exec, create_task, gather
from collections import defaultdict
from contextlib import suppress
from io import BytesIO
from os.path import normpath
from pathlib import Path
from subprocess import PIPE

import jinja2
import panflute
from panflute import Code, Doc, Element, Header, Link, Para, Space, Str, Table, stringify

from sobiraka.models import Anchor, Anchors, BadLink, DirPage, Href, Issue, Page, PageHref, Project, UrlHref, Volume
from sobiraka.models.exceptions import DisableLink
from sobiraka.runtime import RT
from sobiraka.utils import UniqueList, convert_or_none, on_demand, save_debug_json
from .dispatcher import Dispatcher


class Processor(Dispatcher):
    def __init__(self):
        self.jinja: dict[Volume, jinja2.Environment] = {}

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

        self.process2_tasks: dict[Page, list[Task]] = defaultdict(list)
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

        variables = page.volume.config.variables | {
            'toc': SubtreeToc(self, page),
            'LANG': page.volume.lang,
        }

        page_text = page.text

        if page.volume not in self.jinja:
            self.jinja[page.volume] = jinja2.Environment(
                comment_start_string='{{#',
                comment_end_string='#}}',
                enable_async=True,
                loader=convert_or_none(jinja2.FileSystemLoader, page.volume.config.paths.partials),
            )
        page_text = await self.jinja[page.volume].from_string(page_text).render_async(variables)

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

    async def process_header(self, header: Header, page: Page) -> tuple[Element, ...]:
        if not header.identifier:
            header.identifier = stringify(header)
            header.identifier = header.identifier.lower()
            header.identifier = re.sub(r'\W+', '-', header.identifier)

        anchor = Anchor(header.identifier, stringify(header), header)
        self.anchors[page].append(anchor)

        if header.level == 1:
            self.titles[page] = stringify(header)

        return (header,)

    async def process_para(self, para: Para, page: Page) -> tuple[Element, ...]:
        with suppress(AssertionError):
            assert len(para.content) >= 1
            assert isinstance(para.content[0], Str)
            assert para.content[0].text.startswith('//')

            text = ''
            for elem in para.content:
                assert isinstance(elem, (Str, Space))
                text += stringify(elem)

            if m := re.fullmatch(r'// table-id: (\S+)', text):
                table_id = m.group(1)
                table = para.next
                if not isinstance(table, Table):
                    raise RuntimeError(f'Wait, where is the table? [{table_id}]')
                RT.IDS[id(table)] = table_id
                return ()

        return await super().process_para(para, page)

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

    async def process_link(self, link: Link, page: Page):
        if re.match(r'^\w+:', link.url):
            self.links[page].append(UrlHref(link.url))
        else:
            if page.path_in_volume.suffix == '.rst':
                self.issues[page].append(BadLink(link.url))
                return
            await self._process_internal_link(link, link.url, page)

    async def process_role_doc(self, code: Code, page: Page):
        if m := re.fullmatch(r'(.+) < (.+) >', code.text, flags=re.X):
            label = m.group(1).strip()
            target_text = m.group(2)
        else:
            label = None
            target_text = code.text

        link = Link(Str(label))
        await self._process_internal_link(link, target_text, page)
        return (link,)

    async def _process_internal_link(self, elem: Link, target_text: str, page: Page):
        try:
            m = re.fullmatch(r'(?: \$ ([A-z0-9\-_]+)? )? (/)? ([^#]+)? (?: [#] (.+) )?$', target_text, re.VERBOSE)
            volume_name, is_absolute, target_path_str, target_anchor = m.groups()

            if (volume_name, is_absolute, target_path_str) == (None, None, None):
                target = page

            else:
                volume = page.volume
                if volume_name is not None:
                    volume = page.volume.project.get_volume(volume_name)
                    is_absolute = True

                target_path = Path(target_path_str or '.')
                if not is_absolute:
                    if isinstance(page, DirPage):
                        target_path = (page.path_in_volume / target_path).resolve()
                    else:
                        target_path = Path(normpath(page.path_in_volume.parent / target_path))

                target = volume.pages_by_path[target_path]

            href = PageHref(target, target_anchor)
            self.links[page].append(href)

            self.process2_tasks[page].append(create_task(
                self.process2_internal_link(elem, href, target_text, page)
            ))

        except (KeyError, ValueError):
            self.issues[page].append(BadLink(target_text))

    async def process2_internal_link(self, elem: Link, href: PageHref, target_text: str, page: Page):
        await self.process1(href.target)
        try:
            elem.url = self.make_internal_url(href, page=page)
        except DisableLink:
            i = elem.parent.content.index(elem)
            elem.parent.content[i:i + 1] = elem.content
            return

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
