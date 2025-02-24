from __future__ import annotations

from asyncio import Task, create_task
from collections import defaultdict
from typing import TYPE_CHECKING, final

from sobiraka.models import Page, PageStatus, Volume
from sobiraka.models.exceptions import DependencyFailed, IssuesOccurred, VolumeFailed
from sobiraka.report import update_progressbar
from sobiraka.runtime import RT
from sobiraka.utils import super_gather

if TYPE_CHECKING:
    from .builder import Builder


class Waiter:
    def __init__(self, builder: Builder):
        self.builder: Builder = builder

        self._page_tasks: dict[Page, dict[PageStatus, Task]] = defaultdict(dict)
        self._volume_tasks: dict[Volume, Task] = {}

    # region Creating tasks

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
        no matter how many timed the higher-level `wait()` function is called.
        """
        if status is PageStatus.PROCESS3:
            return self.create_volume_task(page.volume)

        try:
            return self._page_tasks[page][status]
        except KeyError as exc:
            match status:
                case PageStatus.PREPARE:
                    coro = self.builder.prepare(page)
                case PageStatus.PROCESS1:
                    coro = self.builder.process1(page)
                case PageStatus.PROCESS2:
                    coro = self.builder.process2(page)
                case PageStatus.PROCESS4:
                    coro = self.builder.process4(page)
                case _:
                    raise ValueError(status) from exc
            task = create_task(coro, name=f'{status.name} {page.path_in_project}')
            self._page_tasks[page][status] = task
            return task

    @final
    def create_volume_task(self, volume: Volume) -> Task:
        try:
            return self._volume_tasks[volume]
        except KeyError:
            coro = self.builder.process3(volume)
            task = create_task(coro, name=f'PROCESS3 {volume.autoprefix}')
            self._volume_tasks[volume] = task
            return task

    # endregion

    # region Awaiting specified statuses

    @final
    async def wait(self, page: Page, target_status: PageStatus):
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
                    before_process3.append(create_task(self.wait(other_page, PageStatus.PROCESS2),
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
            # In the (completely normal) case when multiple copies of `wait()` are running simultaneously
            # for the same page and target status, they all will be awaiting the same Task here.
            # And any future copies of `wait()` will go through this line instantaneously,
            # because the Task will already be finished.
            try:
                await self.create_page_task(page, status)

            # The only place that raises IssuesOccurred is `wait()` itself, see a few lines below.
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

    # endregion
