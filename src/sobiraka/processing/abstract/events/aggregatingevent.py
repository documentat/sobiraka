from asyncio import Event, Task, create_task

from typing_extensions import override

from sobiraka.models import Source
from .preventableevent import PreventableEvent


class AggregatingEvent(Event):
    """
    An event that depends on tasks and events.

    The tasks passed to add_dependency() all must finish, or the event won't fire.

    The events passed to add_page_event() are PreventableEvents,
    and some or all of them may end up failing instead of succeeding.
    As soon as at least one of them succeeds, the AggregatingEvent can fire,
    and it will set the given Source's subtree_has_pages to True.
    If no event succeeds, it's okay too, but the AggregatingEvent will wait for all of them to make sure.
    """

    def __init__(self, source: Source):
        super().__init__()
        self._source: Source = source
        self._dependencies: list[Task] = []
        self._page_events: list[PreventableEvent] = []

    def add_dependency(self, task: Task):
        self._dependencies.append(task)
        task.add_done_callback(self._on_change)

    def add_page_event(self, event: PreventableEvent):
        self._page_events.append(event)
        task = create_task(event.wait())
        task.add_done_callback(lambda t: t.exception())
        task.add_done_callback(self._on_change)

    def _on_change(self, _=None):
        for task in self._dependencies:
            if not task.done():
                return

        still_running = False
        page_generated = False
        for event in self._page_events:
            if not event.is_set():
                still_running = True
            elif event.exception is None:
                page_generated = True
                self._source.subtree_has_pages = True

        if not still_running or page_generated:
            self.set()

    @override
    async def wait(self):
        self._on_change()
        await super().wait()
