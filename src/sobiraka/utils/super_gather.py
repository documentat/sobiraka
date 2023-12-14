from asyncio import Task, gather


async def super_gather(tasks: list[Task]):
    while len(tasks) > 0:
        tasks_length = len(tasks)
        await gather(*tasks)
        tasks = tasks[tasks_length:]
