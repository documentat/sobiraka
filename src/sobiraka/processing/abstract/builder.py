import shlex
from abc import ABCMeta, abstractmethod
from asyncio import Task, create_subprocess_exec, create_task
from collections import defaultdict
from functools import partial
from io import BytesIO
from subprocess import PIPE
from typing import Awaitable, TypeVar, final

import jinja2
import panflute
from jinja2 import StrictUndefined
from panflute import Cite, Doc, Para, Space, Str, stringify

from sobiraka.models import FileSystem, Page, PageHref, Project, Volume
from sobiraka.models.config import Config
from sobiraka.runtime import RT
from sobiraka.utils import super_gather
from .processor import Processor
from .theme import Theme
from ..numerate import numerate

T = TypeVar('T', bound=Theme)
P = TypeVar('P', bound=Processor)


class Builder(metaclass=ABCMeta):
    def __init__(self):
        super().__init__()

        from .waiter import Waiter
        self.waiter: Waiter = Waiter(self)

        self.jinja: dict[Volume, jinja2.Environment] = {}
        self.process2_tasks: dict[Page, list[Task]] = defaultdict(list)

    def __repr__(self):
        return f'<{self.__class__.__name__} at {hex(id(self))}>'

    @abstractmethod
    async def run(self):
        ...

    @abstractmethod
    def get_project(self) -> Project:
        ...

    @abstractmethod
    def get_volumes(self) -> tuple[Volume, ...]:
        ...

    @abstractmethod
    def get_pages(self) -> tuple[Page, ...]:
        ...

    @abstractmethod
    def get_processor_for_page(self, page: Page) -> P:
        ...

    @abstractmethod
    def additional_variables(self) -> dict:
        ...

    async def prepare(self, page: Page):
        """
        Parse syntax tree with Pandoc and save its syntax tree into :obj:`.Page.doc`.

        This method is called by :obj:`.Page.loaded`.
        """
        volume: Volume = page.volume
        config: Config = page.volume.config
        project: Project = page.volume.project
        fs: FileSystem = page.volume.project.fs

        default_variables = dict(
            page=page,
            volume=volume,
            project=project,
            LANG=volume.lang,

            # Format-specific variables
            HTML=False,
            LATEX=False,
            PDF=False,
            PROVER=False,
            WEASYPRINT=False,
            WEB=False,
        )
        variables = config.variables | default_variables | self.additional_variables()

        page_text = page.text

        if volume not in self.jinja:
            self.jinja[volume] = jinja2.Environment(
                comment_start_string='{{#',
                comment_end_string='#}}',
                undefined=StrictUndefined,
                enable_async=True,
                loader=config.paths.partials and jinja2.FileSystemLoader(fs.resolve(config.paths.partials)),
            )
        page_text = await self.jinja[volume].from_string(page_text).render_async(variables)

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

    async def process1(self, page: Page) -> Page:
        """
        Run first pass of page processing.

        Internally, this function runs :func:`process_element()` on the :obj:`.Page.doc` root.

        This method is called by :obj:`.Page.processed1`.
        """
        RT[page].doc.walk(partial(self.preprocess, page=page))
        processor = self.get_processor_for_page(page)
        await processor.process_doc(RT[page].doc, page)
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
            case '@local_toc':
                from ..directive import LocalTocDirective
                return LocalTocDirective(self, page, argv)
            case '@toc':
                from ..directive import TocDirective
                return TocDirective(self, page, argv)

    async def process2(self, page: Page):
        await super_gather(self.process2_tasks[page], f'Additional tasks failed for {page.path_in_project}')

    async def process3(self, volume: Volume):
        if volume.config.content.numeration:
            numerate(volume)

        for page in volume.pages:
            processor = self.get_processor_for_page(page)
            for toc_placeholder in processor.directives[page]:
                toc_placeholder.postprocess()

    async def process4(self, page: Page):
        pass

    @final
    def schedule_for_stage2(self, page: Page, awaitable: Awaitable[None]):
        self.process2_tasks[page].append(create_task(awaitable))

    @abstractmethod
    def make_internal_url(self, href: PageHref, *, page: Page = None) -> str:
        ...
