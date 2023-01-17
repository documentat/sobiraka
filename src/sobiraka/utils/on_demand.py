from asyncio import create_task, Task


class _OnDemandInstance:
    def __init__(self, function):
        self._function = function
        self._task: Task | None = None

    def __await__(self):
        self.start()
        return self._task.__await__()

    def start(self):
        if self._task is None:
            self._task = create_task(self._function())


def on_demand(function):
    aods = {}

    def wrapper(*args):
        try:
            aod = aods[args]
        except KeyError:
            aod = aods[args] = _OnDemandInstance(lambda: function(*args))
        return aod

    return wrapper
