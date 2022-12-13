import asyncio
import inspect
from functools import wraps, partial



def to_async_func(func):
    if inspect.iscoroutinefunction(func):
        return func

    @wraps(func)
    async def run(*args, **kwargs):
        return await asyncio.get_event_loop().run_in_executor(None, partial(func, *args, **kwargs))

    return run

class AsyncResEvent(asyncio.Event):
    def __init__(self):
        super().__init__()
        self.res = None

    def set(self, data=None) -> None:
        self.res = data
        super().set()

    async def wait(self, timeout: float | None = None):
        await super().wait()
        return self.res


class AsyncEvtList:

    def __init__(self):
        self.queue = [AsyncResEvent()]

    def put(self, data):
        if not self.queue or self.queue[-1].is_set():
            self.queue.append(AsyncResEvent())
        self.queue[-1].set(data)

    async def get(self):
        if not self.queue:
            self.queue.append(AsyncResEvent())
        evt = self.queue[0]
        res = await evt.wait()
        if self.queue and self.queue[0] is evt:
            self.queue.pop(0)
        return res
