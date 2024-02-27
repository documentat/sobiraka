import re
import shlex
import sys
from abc import abstractmethod
from asyncio import Task, create_subprocess_exec, create_task, gather
from collections import defaultdict
from contextlib import suppress
from functools import partial
from io import BytesIO
from os.path import normpath
from pathlib import Path
from subprocess import PIPE
from typing import TYPE_CHECKING

import jinja2
import panflute
from jinja2 import StrictUndefined
from panflute import Cite, Code, Doc, Element, Header, Image, Link, Para, Space, Str, Table, stringify

from sobiraka.models import Anchor, BadLink, DirPage, Page, PageHref, Project, UrlHref, Volume
from sobiraka.models.exceptions import DisableLink
from sobiraka.runtime import RT
from sobiraka.utils import convert_or_none, on_demand, super_gather
from .dispatcher import Dispatcher
from ..numerate import numerate

if TYPE_CHECKING:
    from ..directive import TocDirective


class Processor(Dispatcher):
    # pylint: disable=too-many-instance-attributes
    def __init__(self):

        self.jinja: dict[Volume, jinja2.Environment] = {}

        self.process2_tasks: dict[Page, list[Task]] = defaultdict(list)
        self.toc_placeholders: dict[Page, list[TocDirective]] = defaultdict(list)

    def __repr__(self):
        return f'<{self.__class__.__name__} at {hex(id(self))}>'

    @abstractmethod
    def get_pages(self) -> tuple[Page, ...]:
        ...

    @on_demand
    async def load_page(self, page: Page):
        """
        Parse syntax tree with Pandoc and save its syntax tree into :obj:`.Page.doc`.

        This method is called by :obj:`.Page.loaded`.
        """
        from sobiraka.processing import HtmlBuilder
        from sobiraka.processing import PdfBuilder

        variables = page.volume.config.variables | dict(
            HTML=isinstance(self, HtmlBuilder),
            PDF=isinstance(self, PdfBuilder),

            page=page,
            volume=page.volume,
            project=page.volume.project,
            LANG=page.volume.lang,
        )

        page_text = page.text

        if page.volume not in self.jinja:
            self.jinja[page.volume] = jinja2.Environment(
                comment_start_string='{{#',
                comment_end_string='#}}',
                undefined=StrictUndefined,
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

        RT[page].title = page.stem
        RT[page].doc = panflute.load(BytesIO(json_bytes))

    async def get_title(self, page: Page) -> str:
        # TODO: maybe make get_title() a separate @on_demand step?
        await self.process1(page)
        if RT[page].title is None:
            RT[page].title = page.id_segment()
        return RT[page].title

    @on_demand
    async def process1(self, page: Page) -> Page:
        """
        Run first pass of page processing.

        Internally, this function runs :func:`process_element()` on the :obj:`.Page.doc` root.

        This method is called by :obj:`.Page.processed1`.
        """
        await self.load_page(page)
        RT[page].doc.walk(partial(self.preprocess, page=page))
        await self.process_doc(RT[page].doc, page)
        return page

    def preprocess(self, para: Para, _: Doc, *, page: Page):
        try:
            assert isinstance(para, Para)
            assert isinstance(para.content[0], Cite)
        except AssertionError:
            return None

        line = ''
        for item in para.content[1:]:
            match item:
                case Str():
                    line += item.text
                case Space():
                    line += ' '
                case _:
                    raise TypeError(item)
        argv = shlex.split(line)

        match stringify(para.content[0]):
            case '@toc':
                from ..directive import TocDirective
                return TocDirective(self, page, argv)

    async def process_header(self, header: Header, page: Page) -> tuple[Element, ...]:
        if not header.identifier:
            header.identifier = stringify(header)
            header.identifier = header.identifier.lower()
            header.identifier = re.sub(r'\W+', '-', header.identifier)

        # If this is a top level header, use it as the page title
        if header.level == 1:
            RT[page].title = stringify(header)
            if 'unnumbered' in header.classes:
                RT[page].skip_numeration = True

        else:
            anchor = Anchor.from_header(header)
            if 'unnumbered' in header.classes:
                RT[anchor].skip_numeration = True
            RT[page].anchors.append(anchor)

        return (header,)

    async def process_image(self, image: Image, page: Page) -> tuple[Element, ...]:
        """
        Get the image path, process variables inside it, and make it relative to the project directory.
        """
        volume = page.volume

        path = Path(image.url.replace('$LANG', volume.lang or ''))
        if path.is_absolute():
            path = path.relative_to('/')
        else:
            fakeroot = Path('/FAKEROOT')
            path = fakeroot / page.path_in_project.parent / path
            path = Path(normpath(path))
            path = path.relative_to(fakeroot / volume.config.paths.resources)
        image.url = str(path)
        return (image,)

    async def process_para(self, para: Para, page: Page) -> tuple[Element, ...]:
        para, = await super().process_para(para, page)
        assert isinstance(para, Para)

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

        return (para,)

    @on_demand
    async def process2(self, page: Page):
        await self.process1(page)

        await gather(self.process1(page),
                     *(self.process1(dep) for dep in RT[page].dependencies))

        await super_gather(self.process2_tasks[page])

    @on_demand
    async def process3(self, volume: Volume):
        for page in volume.pages:
            self.process2(page).start()
        await gather(*map(self.process2, volume.pages))

        if volume.config.content.numeration:
            numerate(volume.root_page.children)

        for page in volume.pages:
            for toc_placeholder in self.toc_placeholders[page]:
                toc_placeholder.postprocess()

    def print_issues(self) -> bool:
        issues_found: bool = False
        for page in self.get_pages():
            if RT[page].issues:
                message = f'Issues in {page.path_in_project}:'
                for issue in RT[page].issues:
                    message += f'\n    {issue}'
                message += '\n'
                print(message, file=sys.stderr)
                issues_found = True
        return issues_found

    # --------------------------------------------------------------------------------
    # Internal links

    async def process_link(self, link: Link, page: Page):
        if re.match(r'^\w+:', link.url):
            RT[page].links.append(UrlHref(link.url))
        else:
            if page.path_in_volume.suffix == '.rst':
                RT[page].issues.append(BadLink(link.url))
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
            RT[page].links.append(href)

            RT[page].dependencies.add(href.target)
            self.schedule_processing_internal_link(elem, href, target_text, page)

        except (KeyError, ValueError):
            RT[page].issues.append(BadLink(target_text))

    def schedule_processing_internal_link(self, elem: Link, href: PageHref, target_text: str, page: Page):
        self.process2_tasks[page].append(create_task(self.process2_internal_link(elem, href, target_text, page)))

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
                anchor = RT[href.target].anchors.by_identifier(href.anchor)
                if not elem.content:
                    elem.content = Str(anchor.label),

            except (KeyError, AssertionError):
                RT[page].issues.append(BadLink(target_text))
                return

        else:
            if not elem.content:
                elem.content = Str(RT[page].title),

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
