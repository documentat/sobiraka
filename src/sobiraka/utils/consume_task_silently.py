from asyncio import Task


def consume_task_silently(task: Task):
    if not task.cancelled():
        task.exception()
