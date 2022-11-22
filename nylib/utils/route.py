import dataclasses
import inspect
import typing

from .call_hook import BroadcastHook, BroadcastHookAsync
from .asyncio import to_async_func


class KeyRoute:
    hook_type = BroadcastHook
    route: typing.Dict[typing.Any, hook_type]

    def __init__(self, get_key=lambda v: v):
        self.get_key = get_key
        self.route = {}
        self._default_call = None

    def hook(self, key, func=None):
        if func is None:
            return lambda _func: self.hook(key, _func)
        if (hook := self.route.get(key)) is None:
            self.route[key] = hook = self.hook_type()
        if func in hook:
            raise ValueError(f'{func.__name__} is already exists in this hook')
        hook.append(func)
        return KeyRouteItem(self, key, func)

    def unhook(self, key, _func):
        if hook := self.route.get(key):
            hook.remove(_func)

    def __call__(self, *args, **kwargs):
        if hook := self.route.get(self.get_key(*args, **kwargs)):
            hook(*args, **kwargs)
        elif self._default_call:
            self._default_call(*args, **kwargs)

    def default(self, _func):
        self._default_call = _func


class KeyRouteAsync(KeyRoute):
    hook_type = BroadcastHookAsync

    def hook(self, key, func=None):
        if func and not inspect.iscoroutinefunction(func):
            func = to_async_func(func)
        return super().hook(key, func)

    def default(self, _func):
        if _func and not inspect.iscoroutinefunction(_func):
            _func = to_async_func(_func)
        return super().default(_func)

    async def __call__(self, *args, **kwargs):
        if hook := self.route.get(self.get_key(*args, **kwargs)):
            await hook(*args, **kwargs)
        elif self._default_call:
            await self._default_call(*args, **kwargs)


@dataclasses.dataclass
class KeyRouteItem:
    route: 'KeyRoute'
    key: typing.Any
    func: typing.Callable

    def hook(self):
        self.route.hook(self.key, self.func)

    def unhook(self):
        self.route.unhook(self.key, self.func)
