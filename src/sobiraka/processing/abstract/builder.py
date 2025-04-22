from __future__ import annotations

import shlex
from abc import ABCMeta, abstractmethod
from asyncio import Task, create_subprocess_exec, wait
from collections import defaultdict
from functools import partial
from io import BytesIO
from subprocess import PIPE
from typing import Generic, TYPE_CHECKING, TypeVar, final

import jinja2
import panflute
from jinja2 import StrictUndefined
from panflute import Cite, Doc, Para, Space, Str, stringify

from sobiraka.models import FileSystem, Page, PageHref, Project, Source, Status, Volume
from sobiraka.models.config import Config
from sobiraka.runtime import RT
from ..numerate import numerate

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from .processor import Processor
    from .waiter import Waiter

P = TypeVar('P', bound='Processor')


class Builder(Generic[P], metaclass=ABCMeta):
    def __init__(self):
        self.waiter: Waiter | None = None
        self.jinja: dict[Volume, jinja2.Environment] = {}
        self.referencing_tasks: dict[Page, list[Task]] = defaultdict(list)

    def init_waiter(self, target_status: Status) -> Waiter:
        from .waiter import Waiter

        self.waiter = Waiter(self, target_status)
        return self.waiter

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

    @final
    def get_roots(self) -> tuple[Source, ...]:
        return tuple(v.root for v in self.get_volumes())

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
        Parse the syntax tree with Pandoc and save its syntax tree into `RT[page].doc`.
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

        RT[page].doc = panflute.load(BytesIO(json_bytes))

    async def do_process(self, page: Page) -> Page:
        """
        The first stage of page processing.

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

    async def do_reference(self, page: Page):
        """
        The second stage of the processing.
        """
        if self.referencing_tasks[page]:
            await wait(self.referencing_tasks[page])

    async def do_numerate(self, volume: Volume):
        """
        The third stage of the processing.
        Unlike other stages, this deals with the Volume as a whole.
        """
        if volume.config.content.numeration:
            numerate(volume)

        for page in volume.root.all_pages():
            processor = self.get_processor_for_page(page)
            for toc_placeholder in processor.directives[page]:
                toc_placeholder.postprocess()

    async def do_finalize(self, page: Page):
        """
        The fourth stage of the processing.
        """

    @abstractmethod
    def make_internal_url(self, href: PageHref, *, page: Page = None) -> str:
        ...
