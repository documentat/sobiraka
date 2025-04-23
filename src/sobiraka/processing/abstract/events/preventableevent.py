from asyncio import Event

from typing_extensions import override


class PreventableEvent(Event):
    """
    An event with two possible wait() outcomes instead of one:
    maybe someone calls set(), and you successfully continue,
    but maybe someone calls fail(), and you get an exception.
    """

    def __init__(self):
        super().__init__()
        self.exception: BaseException | type[BaseException] | None = None

    def fail(self, exception: BaseException | type[BaseException]):
        if self.is_set():
            return
        self.exception = exception
        super().set()

    @override
    async def wait(self):
        await super().wait()
        if self.exception is not None:
            raise self.exception
