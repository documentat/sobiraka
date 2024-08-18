from asyncio import Task, gather
from typing import Sequence


async def super_gather(tasks: Sequence[Task], error_message: str = 'Not all tasks gathered here'):
    """
    Wait for all `tasks`, even the ones that will be added there after we begin.
    Each task is guaranteed to be awaited till it finishes.
    All exceptions will be collected and reraised as an ExceptionGroup with the given message.
    """
    from sobiraka.models.exceptions import Ignorable

    tasks = list(tasks)
    exceptions = []

    while len(tasks) != 0:
        length = len(tasks)

        results = await gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception) and not isinstance(result, Ignorable):
                exceptions.append(result)

        tasks = tasks[length:]

    if len(exceptions) != 0:
        raise ExceptionGroup(error_message, exceptions)
