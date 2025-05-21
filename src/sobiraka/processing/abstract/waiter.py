from asyncio import Task, create_task, get_event_loop, sleep, wait
from collections import defaultdict
from itertools import chain
from typing import Coroutine, Sequence, TYPE_CHECKING, overload

from sobiraka.models import AggregationPolicy, Issue, Page, Source, Status, Volume
from sobiraka.report import Reporter
from sobiraka.utils import KeyDefaultDict, MISSING, RelativePath, print_colorful_exc, sorted_dict
from .events import AggregatingEvent, PreventableEvent, ProductiveEvent

if TYPE_CHECKING:
    from .builder import Builder


class Waiter:
    """
    This class is the most important part of the implementation of Builder.
    It manages RelativePaths, Sources, Pages, and the asynchronous tasks and events for processing them.
    When initialized, a Waiter is given the status which all pages are expected to get eventually.

    As far as any other code is concerned, there are just two methods here:
      - `start()` for launching the tasks,
      - `wait()` for waiting until a certain page gets a certain status,
      - `wait_all()` for waiting until all pages get the target status.
    """

    def __init__(self, builder: 'Builder', target_status: Status = Status.FINALIZE):
        self.builder: Builder = builder
        self.target_status: Status = target_status

        self.tasks: dict[Source | Page, dict[Status, Task]] = defaultdict(dict)
        self.tasks_p3: dict[Volume, Task] = {}
        self.additional_tasks: list[Task] = []

        self.aggregating: dict[Source, AggregatingEvent] = KeyDefaultDict(AggregatingEvent)
        self.path_events: dict[RelativePath, ProductiveEvent[Source]] = defaultdict(ProductiveEvent)
        self.page_events: dict[Source, PreventableEvent] = defaultdict(PreventableEvent)

        self.done = PreventableEvent()

    # ------------------------------------------------------------------------------------------------------------------
    # region Public interface

    def start(self):
        for root in self.builder.get_roots():
            Reporter.register_volume(root.volume)
            self.schedule_tasks(root, self.target_status)
        assert self.tasks

    def add_task(self, coro: Coroutine):
        task = create_task(coro, name=coro.__name__)
        task.add_done_callback(self.maybe_done)
        self.additional_tasks.append(task)

    async def wait_all(self):
        if not self.tasks:
            self.start()
        await self.done.wait()

    @overload
    async def wait(self, path: RelativePath, target_status: Status, /) -> Source:
        ...

    @overload
    async def wait(self, source: Source, target_status: Status, /) -> Source:
        ...

    @overload
    async def wait(self, page: Page, target_status: Status, /) -> Page:
        ...

    async def wait(self, obj: RelativePath | Source | Page, status: Status, /) -> Source | Page:
        """
        Perform all yet unperformed operations until the `page` reaches the given status.
        """
        if isinstance(obj, RelativePath):
            obj = await self.path_events[obj].wait()

        self.schedule_tasks(obj, status)
        await self.tasks[obj][status]
        return obj

    # endregion

    # ------------------------------------------------------------------------------------------------------------------
    # region Scheduling new tasks

    def schedule_tasks(self, obj: Source | Page, target_status: Status):
        """
        Schedule zero or more new tasks that need to be performed
        to get a Source or a Page from its current status to the specified status.

        Can be safely called as many times as you want.
        """
        match obj:
            case Source():
                self.schedule_tasks_for_source(obj, target_status)
            case Page():
                self.schedule_tasks_for_page(obj, target_status)
            case _:
                raise TypeError(obj)

    def schedule_tasks_for_source(self, source: Source, target_status: Status):
        """
        A part of the implementation of schedule_tasks().

        Ensures that all necessary tasks are created to get the Source to target_status.
        If a task already exists for a certain status, its creation will be skipped.
        """
        for status in Status.range(Status.DISCOVER, target_status):
            if status in self.tasks[source]:
                continue

            # Choose a coroutine for the status
            match status:
                case Status.LOAD:
                    coro = self.do_load(source)
                case _:
                    coro = self.do_process_source(source, status)

            # Create a task
            task = create_task(coro, name=f'{status.name} SOURCE {source.path_in_project}')
            self.tasks[source][status] = task

    def schedule_tasks_for_page(self, page: Page, target_status: Status):
        """
        A part of the implementation of schedule_tasks().

        Ensures that all necessary tasks are created to get the Page to target_status.
        If a task already exists for a certain status, its creation will be skipped.
        """
        for status in Status.range(Status.DISCOVER, target_status):
            if status in self.tasks[page]:
                continue

            if status is Status.NUMERATE:
                # NUMERATE is a special step that must be performed once on the whole Volume.
                # So, we create the task only when we first need it.
                # Then we store it in `tasks_p3` and reuse many times in `tasks`.
                try:
                    self.tasks[page][Status.NUMERATE] = self.tasks_p3[page.volume]

                except KeyError:
                    task = create_task(self.do_numerate_volume(page.volume),
                                       name=f'NUMERATE VOLUME {page.volume.codename}')
                    self.tasks[page][Status.NUMERATE] = task
                    self.tasks_p3[page.volume] = task

            else:
                # All other tasks are page-specific,
                # so we just create a task and store it in `tasks`
                self.tasks[page][status] = create_task(self.do_process_page(page, status),
                                                       name=f'{status.name} PAGE {page.location}')

    # endregion

    # ------------------------------------------------------------------------------------------------------------------
    # region Actual code for processing content

    async def do_load(self, source: Source):
        """
        This method calls the source's methods for generating child sources and pages,
        schedules new tasks for everything that was generated,
        and adds corresponding dependencies to its parents if necessary.

        By the end of this method, the source gets the LOAD status.

        This method must be called exactly one time per one source.
        """
        try:
            # Let the source populate its child_sources list
            await source.generate_child_sources()
            assert source.child_sources is not MISSING, \
                f'Source {source.path_in_project} failed to generate child sources.'
            Reporter.register_child_sources(source)

            # Schedule all tasks for the child sources and connect its tasks and events
            # to the AggregatingEvents for the current source and its parents.
            # To avoid any weird behavior, it is important to finish setting the dependencies
            # before any child tasks actually start: notice the lack of `await` keywords here.
            for child in source.child_sources:
                self.schedule_tasks(child, self.target_status)

                if AggregationPolicy.WAIT_FOR_CHILDREN in source.aggregation_policy:
                    self.aggregating[source].add_dependency(self.tasks[child][Status.LOAD])

                for crumb in source.breadcrumbs:
                    if AggregationPolicy.WAIT_FOR_SUBTREE in crumb.aggregation_policy:
                        self.aggregating[crumb].add_dependency(self.tasks[child][Status.LOAD])
                    if AggregationPolicy.WAIT_FOR_ANY_PAGE in crumb.aggregation_policy:
                        self.aggregating[crumb].add_page_event(self.page_events[child])

            # The AggregatingEvent is now properly configured. Await it.
            await self.aggregating[source].wait()

            # Let the source populate its pages list
            await source.generate_pages()
            assert source.pages is not MISSING, f'Source {source.path_in_project} failed to generate pages.'
            for page in source.pages:
                assert page.children is not MISSING, f'Page {page.location} does not have a children list.'
            Reporter.register_pages(source)

            # Schedule all tasks for the pages
            for page in source.pages:
                assert page.children is not MISSING, \
                    f'Page {page.location} has empty children list.'
                self.schedule_tasks(page, self.target_status)

            # Loading this source is complete
            source.status = Status.LOAD

            # Notify others about whether this source has generated any pages.
            # This event may be awaited by other sources' AggregatingEvents.
            if source.pages:
                self.page_events[source].set()
            else:
                self.page_events[source].fail(NoPagesGeneratedFromSource(source))

            # If anyone was looking for this source by its path, they may now proceed
            self.path_events[source.path_in_project].set_result(source)

        except DependencyFailed:
            source.status = Status.DEP_FAILURE
            raise

        except Exception as exc:
            print_colorful_exc()
            source.status = Status.SOURCE_FAILURE
            source.exception = exc
            raise DependencyFailed(exc) from exc

        finally:
            self.maybe_done()

    async def do_process_source(self, source: Source, status: Status):
        """
        Make sure the given source has generated its pages,
        then make sure the pages reach the requested status.

        This method can be called multiple times (though in fact it is only called once).
        """
        try:
            # Wait until the source is loaded
            await self.tasks[source][Status.LOAD]

            # Wait until all the pages get the required status
            if source.pages:
                await wait([self.tasks[p][status] for p in source.pages])

        finally:
            self.maybe_done()

    async def do_process_page(self, page: Page, status: Status):
        """
        Run the Builder's processing function for the given status on the given page.
        Remember any issues or exceptions if they occur.

        This method must be called exactly one time per one page.
        """

        # Wait for the previous status
        if status.prev is not Status.DISCOVER:
            await self.tasks[page][status.prev]

        # Select the processing function to run
        match status:
            case Status.LOAD:
                coro = sleep(0)
            case Status.PARSE:
                coro = self.builder.prepare(page)
            case Status.PROCESS:
                coro = self.builder.do_process(page)
            case Status.REFERENCE:
                coro = self.builder.do_reference(page)
            case Status.FINALIZE:
                coro = self.builder.do_finalize(page)
            case _:
                raise ValueError(status)

        try:
            # Run the selected function
            await coro

            if page.issues:
                raise IssuesOccurred(page.source.path_in_project, page.issues)
            if page.exception:
                raise page.exception

            page.status = status

        except DependencyFailed:
            page.status = Status.DEP_FAILURE
            raise

        except IssuesOccurred:
            page.status = Status.PAGE_FAILURE
            raise

        except Exception as exc:
            print_colorful_exc()
            page.status = Status.PAGE_FAILURE
            page.exception = exc
            raise DependencyFailed(exc) from exc

        finally:
            self.maybe_done()

    async def do_numerate_volume(self, volume: Volume):
        """
        Run the Builder's function for the NUMERATE status on the given volume.
        Remember any issues or exceptions if they occur.

        This method must be called exactly one time per one page.
        """
        try:
            await self.wait_recursively(volume.root, Status.REFERENCE)
            await self.builder.do_numerate(volume)
            self.set_status_recursively(volume, Status.NUMERATE)

        except DependencyFailed:
            self.set_status_recursively(volume, Status.DEP_FAILURE)
            raise

        except Exception as exc:
            print_colorful_exc()
            self.set_status_recursively(volume, Status.VOL_FAILURE)
            volume.root.exception = exc
            raise DependencyFailed(exc) from exc

        finally:
            self.maybe_done()

    # endregion

    # ------------------------------------------------------------------------------------------------------------------
    # region Checking completion

    def maybe_done(self, _: Task = None):
        """
        Check the statuses of all sources and pages.
        The purpose of this function is to be called after each status change,
        i.e., at the end of every `do_*()` function.

        If all of them got the required status, consider it a success.
        If some of them raised issues or exceptions, consider it a failure.
        This information will be received by the code that called `wait_all()`.

        If the generation or processing is not completed yet, this function will do nothing.
        """
        get_event_loop().call_soon(self.maybe_done_impl)

    def maybe_done_impl(self):
        # pylint: disable=too-many-branches
        still_loading = False
        still_processing = False
        excs: dict[RelativePath | None, list[BaseException]] = defaultdict(list)

        # We start by iterating over just the roots,
        # but we will be adding all children to the queue as we go
        queue: list[Source] = list(self.builder.get_roots())
        while queue:
            source = queue.pop(0)
            if source.child_sources is not MISSING:
                queue += source.child_sources

            # If the source has not yet generated its children and pages, do nothing
            if source.status == Status.DISCOVER:
                still_loading = True
                still_processing = True
                continue

            # If we have a failure, remember this fact
            if source.exception:
                excs[source.path_in_project].append(source.exception)
            elif source.issues:
                excs[source.path_in_project].append(IssuesOccurred(source.path_in_project, source.issues))
            elif source.status.is_failed():
                excs[source.path_in_project].append(RuntimeError(f'Source status: {source.status.name}.'))

            # Check if the source's pages are ready
            if source.pages is not MISSING:
                for page in source.pages:
                    if page.status < self.target_status:
                        still_processing = True
                    elif page.exception:
                        excs[source.path_in_project].append(page.exception)
                    elif page.issues:
                        excs[source.path_in_project].append(IssuesOccurred(page.source.path_in_project, page.issues))
                    elif page.status.is_failed():
                        excs[source.path_in_project].append(RuntimeError(f'Page status: {page.status.name}.'))

        if not still_processing:
            for task in self.additional_tasks:
                if not task.done():
                    still_processing = True
                    break
                if task.exception() is not None:
                    excs[None].append(task.exception())

        Reporter.refresh()

        # If the generation is complete for all sources,
        # it means that everyone who waited with a Path should have received a Source now.
        # If anyone hasn't, they apparently have an incorrect Path, so raise exceptions for them.
        if not still_loading:
            for path, event in self.path_events.items():
                if not event.is_set():
                    event.fail(NoSourceCreatedForPath(path))

        # If nothing is processing anymore, cancel any unused tasks and trigger the event
        if not still_processing:
            for subdict in self.tasks.values():
                for task in subdict.values():
                    if not task.done():
                        task.cancel()

            if excs:
                excs = sorted_dict(excs, key=lambda k: (k is None, k))
                sorted_exceptions = list(chain(*excs.values()))
                self.done.fail(BuildFailure('Build failure', sorted_exceptions))
            else:
                self.done.set()

    # endregion

    # ------------------------------------------------------------------------------------------------------------------
    # region Helper functions

    async def wait_recursively(self, source: Source, target_status: Status):
        """
        Wait for the given status on:

        - the given source,
        - all of its direct and indirect child sources,
        - all of its direct and indirect generated pages.
        """

        # Make sure child sources and pages are discovered
        await self.tasks[source][Status.LOAD]

        aws = []

        for child in source.child_sources:
            aws.append(create_task(self.wait_recursively(child, target_status)))

        for page in source.pages:
            aws.append(self.tasks[page][target_status])

        if aws:
            await wait(aws)

    def set_status_recursively(self, volume: Volume, status: Status):
        """
        Set the given status to all sources and pages in the volume.
        """
        volume.root.status = status

        for child in volume.root.all_child_sources():
            if not child.status.is_failed():
                child.status = status

        for page in volume.root.all_pages():
            if not page.status.is_failed():
                page.status = status

    # endregion


# region Exceptions

class IssuesOccurred(Exception):
    def __init__(self, path: RelativePath, issues: Sequence[Issue]):
        self.path: RelativePath = path
        self.issues: tuple[Issue, ...] = tuple(issues)

        assert len(issues) > 0
        this_many_issues = str(len(issues)) + ' issue' + ('s' if len(issues) > 1 else '')
        message = f'{this_many_issues} occurred in {path}:'
        for issue in issues:
            message += f'\n  {issue}'
        super().__init__(message)


class DependencyFailed(Exception):
    def __init__(self, original_exc: Exception):
        super().__init__()
        self.original_exc = original_exc


class NoSourceCreatedForPath(Exception):
    def __init__(self, path: RelativePath):
        super().__init__(f'No source created for {str(path)!r}')


class NoPagesGeneratedFromSource(Exception):
    def __init__(self, source: Source):
        super().__init__(f'No pages generated from {str(source.path_in_project)!r}')


class BuildFailure(ExceptionGroup):
    pass

# endregion
