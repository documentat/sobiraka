import shlex
from abc import ABCMeta, abstractmethod
from asyncio import Task, create_subprocess_exec, create_task
from collections import defaultdict
from functools import partial
from io import BytesIO
from subprocess import PIPE
from typing import Awaitable, Generic, TypeVar, final

import jinja2
import panflute
from jinja2 import StrictUndefined
from panflute import Cite, Doc, Para, Space, Str, stringify

from sobiraka.models import FileSystem, Page, PageHref, PageStatus, Project, Volume
from sobiraka.models.config import Config
from sobiraka.models.exceptions import DependencyFailed, IssuesOccurred, VolumeFailed
from sobiraka.report import update_progressbar
from sobiraka.runtime import RT
from sobiraka.utils import super_gather
from .processor import Processor
from .theme import Theme
from ..numerate import numerate

T = TypeVar('T', bound=Theme)
P = TypeVar('P', bound=Processor)


class Builder(Generic[P, T], metaclass=ABCMeta):
    def __init__(self):
        self.tasks: dict[Page | Volume, dict[PageStatus, Task]] = defaultdict(dict)
        """
        Dictionary of all tasks that the building has started. Managed by `create_page_task()`.
        """

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

    @final
    def create_page_task(self, page: Page, status: PageStatus) -> Task:
        """
        Creates (if not created) a Task that runs a function corresponding to the given PageStatus.

        - For any status other than `PROCESS3`, the task is created as `self.tasks[page][status]`.

        - For `PROCESS3`, the task is created as `self.tasks[volume][status]`.
          For other pages from the same Volume, the same Task will be returned,
          and no new calls of `process3()` will be made.

        This function is synchronous, so that there is never any confusion
        about which tasks are created and which are not,
        no matter how many timed the higher-level `require()` function is called.
        """
        key = page.volume if status is PageStatus.PROCESS3 else page
        try:
            task = self.tasks[key][status]
        except KeyError as exc:
            match status:
                case PageStatus.PREPARE:
                    coro = self.prepare(page)
                case PageStatus.PROCESS1:
                    coro = self.process1(page)
                case PageStatus.PROCESS2:
                    coro = self.process2(page)
                case PageStatus.PROCESS3:
                    coro = self.process3(page.volume)
                case PageStatus.PROCESS4:
                    coro = self.process4(page)
                case _:
                    raise ValueError(status) from exc
            task = self.tasks[key][status] = create_task(coro, name=f'{status.name} {page.path_in_project}')
        return task

    @final
    async def require(self, page: Page, target_status: PageStatus):
        """
        Perform all yet unperformed operations until the `page` will reach the `target_status`.
        Do nothing if it has that status already.
        """
        # pylint: disable=too-many-branches

        # If the page already got the target status, do nothing
        if RT[page].status is target_status:
            return

        # If the page already failed, raise the corresponding exception
        if RT[page].status is PageStatus.FAILURE:
            raise IssuesOccurred(page, RT[page].issues)
        if RT[page].status is PageStatus.DEP_FAILURE:
            raise DependencyFailed(page)
        if RT[page].status is PageStatus.VOL_FAILURE:
            raise VolumeFailed(page.volume)

        # Decide which statuses we will have to go through to get to the the target
        roadmap: list[PageStatus] = list(filter(lambda s: RT[page].status < s <= target_status, PageStatus))

        # If the roadmap includes or ends with PROCESS3 (the volume-wide step),
        # immediately launch tasks for other pages of the same volume.
        # Later, we will wait for them to finish before we call `process3()` for the volume.
        before_process3: list[Task] = []
        if PageStatus.PROCESS3 in roadmap:
            for other_page in page.volume.pages:
                if other_page is not page:
                    before_process3.append(create_task(self.require(other_page, PageStatus.PROCESS2),
                                                       name=f'require {other_page.path_in_project}'))

        # Iterate from the current status to the required status
        for status in PageStatus.range(RT[page].status, target_status):

            # Special treatment for the volume-wide step: make sure that all pages of the volume are ready.
            # If not, raise VolumeFailed. Note that this type of exception is Ignorable,
            # i.e., it is not really the current page's fault, and thus it is not interesting for the user.
            # Basically, we cannot proceed but we won't explain why: someone else will have explained it already.
            if status is PageStatus.PROCESS3:
                try:
                    await super_gather(before_process3, f'Some other pages failed in {page.volume.codename!r}')
                except* Exception as excs:
                    RT[page].status = PageStatus.VOL_FAILURE
                    update_progressbar()
                    raise VolumeFailed(page.volume) from excs

            # Start running the appropriate function.
            # In the (completely normal) case when multiple copies of `require()` are running simultaneously
            # for the same page and target status, they all will be awaiting the same Task here.
            # And any future copies of `require()` will go through this line instantaneously,
            # because the Task will already be finished.
            try:
                await self.create_page_task(page, status)

            # The only place that raises IssuesOccurred is `require()` itself, see a few lines below.
            # If we catch it, it means that the step required some other page, but processing that page failed.
            # It is an IssuesOccurred for that page, but a DependencyFailed for the current one.
            # The same logic applies to another page's VolumeFailed.
            except* (IssuesOccurred, VolumeFailed) as excs:
                RT[page].status = PageStatus.DEP_FAILURE
                update_progressbar()
                raise DependencyFailed(page) from excs

            # Any other type of exception is unexpected. May even be a Sobiraka bug.
            # We consider it the current page's failure and set the status accordingly.
            except* Exception:
                RT[page].status = PageStatus.FAILURE
                update_progressbar()
                raise

            # If we are still here, update the status
            RT[page].status = status
            update_progressbar()

            # If any number of issues was found for the page, we consider it a failure and raise IssuesOccurred.
            if len(RT[page].issues) != 0:
                RT[page].status = PageStatus.FAILURE
                update_progressbar()
                raise IssuesOccurred(page, RT[page].issues)

    async def prepare(self, page: Page):
        """
        Parse syntax tree with Pandoc and save its syntax tree into :obj:`.Page.doc`.

        This method is called by :obj:`.Page.loaded`.
        """
        from sobiraka.processing.latex import LatexBuilder
        from sobiraka.processing.weasyprint import WeasyPrintBuilder
        from sobiraka.processing.web import WebBuilder, AbstractHtmlBuilder

        volume: Volume = page.volume
        config: Config = page.volume.config
        project: Project = page.volume.project
        fs: FileSystem = page.volume.project.fs

        variables = config.variables | dict(
            HTML=isinstance(self, AbstractHtmlBuilder),
            PDF=isinstance(self, (WeasyPrintBuilder, LatexBuilder)),

            WEB=isinstance(self, WebBuilder),
            WEASYPRINT=isinstance(self, WeasyPrintBuilder),
            LATEX=isinstance(self, LatexBuilder),

            page=page,
            volume=volume,
            project=project,
            LANG=volume.lang,
        )

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


class ProjectBuilder(Builder, Generic[P, T], metaclass=ABCMeta):
    """
    A builder that works with the whole project at once.
    Each volume can still have its own `Processor` and `Theme`, though.
    """

    def __init__(self, project: Project):
        Builder.__init__(self)

        self.project: Project = project
        self.processors: dict[Volume, P] = {}
        self.themes: dict[Volume, T] = {}

        for volume in project.volumes:
            self.processors[volume] = self.init_processor(volume)
            self.themes[volume] = self.init_theme(volume)

    @final
    def get_project(self) -> Project:
        return self.project

    @final
    def get_volumes(self) -> tuple[Volume, ...]:
        return self.project.volumes

    @final
    def get_pages(self) -> tuple[Page, ...]:
        return self.project.pages

    @final
    def get_processor_for_page(self, page: Page) -> P:
        return self.processors[page.volume]

    @abstractmethod
    def init_processor(self, volume: Volume) -> P: ...

    @abstractmethod
    def init_theme(self, volume: Volume) -> T: ...


class VolumeBuilder(Builder, Generic[P, T], metaclass=ABCMeta):
    """
    A builder that works with an individual volume.
    """

    def __init__(self, volume: Volume):
        Builder.__init__(self)
        self.volume: Volume = volume
        self.processor: P = self.init_processor()
        self.theme: T = self.init_theme()

    @final
    def get_project(self) -> Project:
        return self.volume.project

    @final
    def get_volumes(self) -> tuple[Volume, ...]:
        return self.volume,

    @final
    def get_pages(self) -> tuple[Page, ...]:
        return self.volume.pages

    @final
    def get_processor_for_page(self, page: Page) -> P:
        return self.processor

    @abstractmethod
    def init_processor(self) -> P: ...

    @abstractmethod
    def init_theme(self) -> T: ...
