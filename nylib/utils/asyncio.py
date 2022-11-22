import asyncio
from functools import wraps, partial


def to_async_func(func):

    @wraps(func)
    async def run(*args, **kwargs):
        return await asyncio.get_event_loop().run_in_executor(None, partial(func, *args, **kwargs))

    return run
