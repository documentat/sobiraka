import re
import shlex
from abc import abstractmethod
from asyncio import Task, create_subprocess_exec, create_task
from collections import defaultdict
from contextlib import suppress
from functools import partial
from io import BytesIO
from os.path import normpath
from subprocess import PIPE

import jinja2
import panflute
from jinja2 import StrictUndefined
from panflute import Cite, Code, Doc, Element, Header, Image, Link, Para, Space, Str, Table, stringify

from sobiraka.models import Anchor, BadImage, BadLink, DirPage, FileSystem, Page, PageHref, PageStatus, Project, \
    UrlHref, Volume
from sobiraka.models.config import Config
from sobiraka.models.exceptions import DependencyFailed, DisableLink, IssuesOccurred, VolumeFailed
from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath, PathGoesOutsideStartDirectory, RelativePath, absolute_or_relative, super_gather
from .dispatcher import Dispatcher
from ..directive import Directive
from ..numerate import numerate


class Processor(Dispatcher):
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods

    def __init__(self):
        self.message: str = None
        """
        Text message describing what the processor is currently doing.
        Will be displayed next to the progressbar.
        """

        self.tasks: dict[Page | Volume, dict[PageStatus, Task]] = defaultdict(dict)
        """
        Dictionary of all tasks that the processor has started. Managed by `create_page_task()`.
        """

        self.jinja: dict[Volume, jinja2.Environment] = {}

        self.process2_tasks: dict[Page, list[Task]] = defaultdict(list)
        self.directives: dict[Page, list[Directive]] = defaultdict(list)

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
                    raise VolumeFailed(page.volume) from excs

            # Start running the appropriate function.
            # In the (completely normal) case when multiple copies of `require()` are running simultaneously
            # for the same page and target status, they all will be awaiting the same Task here.
            # And any future copies of `require()` will go through this line instantaneously,
            # because the Task will already be finished.
            try:
                await self.create_page_task(page, status)

            # The only place that raises IssuesOccured is `require()` itself, see a few lines below.
            # If we catch it, it means that the step required some other page, but processing that page failed.
            # It is an IssuesOccurred for that page, but a DependencyFailed for the current one.
            # The same logic applies to another page's VolumeFailed.
            except* (IssuesOccurred, VolumeFailed) as excs:
                RT[page].status = PageStatus.DEP_FAILURE
                raise DependencyFailed(page) from excs

            # Any other type of exception is unexpected. May even be a Sobiraka bug.
            # We consider it the current page's failure and set the status accordingly.
            except* Exception:
                RT[page].status = PageStatus.FAILURE
                raise

            # If we are still here, update the status
            RT[page].status = status

            # If any number of issues was found for the page, we consider it a failure and raise IssuesOccurred.
            if len(RT[page].issues) != 0:
                RT[page].status = PageStatus.FAILURE
                raise IssuesOccurred(page, RT[page].issues)

    async def prepare(self, page: Page):
        """
        Parse syntax tree with Pandoc and save its syntax tree into :obj:`.Page.doc`.

        This method is called by :obj:`.Page.loaded`.
        """
        from sobiraka.processing import HtmlBuilder, PdfBuilder

        volume: Volume = page.volume
        config: Config = page.volume.config
        project: Project = page.volume.project
        fs: FileSystem = page.volume.project.fs

        variables = config.variables | dict(
            HTML=isinstance(self, HtmlBuilder),
            PDF=isinstance(self, PdfBuilder),

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
            case '@local_toc':
                from ..directive import LocalTocDirective
                return LocalTocDirective(self, page, argv)
            case '@toc':
                from ..directive import TocDirective
                return TocDirective(self, page, argv)

    async def process_directive(self, directive: Directive, page: Page) -> tuple[Element, ...]:
        self.directives[page].append(directive)
        return await super().process_directive(directive, page)

    async def process_header(self, header: Header, page: Page) -> tuple[Element, ...]:
        # Generate an identifier if is not done automatically, e.g., in RST
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
        Get the image path, process variables inside it, and make it relative to the resources directory.

        If the file does not exist, create an Issue and set `image.url` to None.
        """
        volume: Volume = page.volume
        config: Config = volume.config
        fs: FileSystem = volume.project.fs

        path = image.url.replace('$LANG', volume.lang or '')
        path = absolute_or_relative(path)
        if isinstance(path, AbsolutePath):
            path = path.relative_to('/')
        else:
            path = page.path_in_project.parent / path
            path = RelativePath(normpath(path))
            path = path.relative_to(volume.config.paths.resources)

        if fs.exists(config.paths.resources / path):
            image.url = str(path)
        else:
            RT[page].issues.append(BadImage(image.url))
            image.url = None

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

    async def process2(self, page: Page):
        await super_gather(self.process2_tasks[page], f'Additional tasks failed for {page.path_in_project}')

    async def process3(self, volume: Volume):
        if volume.config.content.numeration:
            numerate(volume.root_page.children)

        for page in volume.pages:
            for toc_placeholder in self.directives[page]:
                toc_placeholder.postprocess()

    async def process4(self, page: Page):
        pass

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

                target_path = RelativePath(target_path_str or '.')
                if not is_absolute:
                    if isinstance(page, DirPage):
                        target_path = (page.path_in_volume / target_path).resolve()
                    else:
                        target_path = RelativePath(normpath(page.path_in_volume.parent / target_path))

                target = volume.pages_by_path[target_path]

            href = PageHref(target, target_anchor)
            RT[page].links.append(href)

            RT[page].dependencies.add(href.target)
            self.schedule_processing_internal_link(elem, href, target_text, page)

        except (KeyError, ValueError, PathGoesOutsideStartDirectory):
            RT[page].issues.append(BadLink(target_text))

    def schedule_processing_internal_link(self, elem: Link, href: PageHref, target_text: str, page: Page):
        self.process2_tasks[page].append(create_task(
            self.process2_internal_link(elem, href, target_text, page)
        ))

    async def process2_internal_link(self, elem: Link, href: PageHref, target_text: str, page: Page):
        await self.require(href.target, PageStatus.PROCESS1)
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
                elem.content = Str(RT[href.target].title),

    @abstractmethod
    def make_internal_url(self, href: PageHref, *, page: Page) -> str:
        ...


class ProjectProcessor(Processor):
    # TODO: add ABCMeta to the base Processor class
    # pylint: disable=abstract-method
    def __init__(self, project: Project):
        super().__init__()
        self.project: Project = project

    def get_project(self) -> Project:
        return self.project

    def get_volumes(self) -> tuple[Volume, ...]:
        return self.project.volumes

    def get_pages(self) -> tuple[Page, ...]:
        return self.project.pages


class VolumeProcessor(Processor):
    # pylint: disable=abstract-method
    def __init__(self, volume: Volume):
        super().__init__()
        self.volume: Volume = volume

    def get_project(self) -> Project:
        return self.volume.project

    def get_volumes(self) -> tuple[Volume, ...]:
        return self.volume,

    def get_pages(self) -> tuple[Page, ...]:
        return self.volume.pages
