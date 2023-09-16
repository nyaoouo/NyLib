import ctypes
import functools
import inspect
import struct
import threading
import pathlib
import time
import typing

_T = typing.TypeVar('_T')
_T2 = typing.TypeVar('_T2')


def count_func_time(func):
    import time

    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        return func(*args, **kwargs), time.perf_counter() - start

    return wrapper


def num_arr_to_bytes(arr):
    return bytes(arr).split(b'\0', 1)[0]


def is_iterable(v):
    try:
        iter(v)
    except TypeError:
        return False
    else:
        return True


class Counter:
    def __init__(self, start=0):
        self.count = start - 1
        self.lock = threading.Lock()

    def get(self):
        with self.lock:
            self.count += 1
            return self.count


def iter_rm(p: pathlib.Path):
    if p.exists():
        if p.is_file():
            p.unlink()
        else:
            for f in p.iterdir():
                iter_rm(f)
            p.rmdir()


def safe(func: typing.Callable[[...], _T], *args, _handle=BaseException, _default: _T2 = None, **kwargs) -> _T | _T2:
    try:
        return func(*args, **kwargs)
    except _handle:
        return _default


def safe_lazy(func: typing.Callable[[...], _T], *args, _handle=BaseException, _default: _T2 = None, **kwargs) -> _T | _T2:
    try:
        return func(*args, **kwargs)
    except _handle:
        return _default(*args, **kwargs)


time_units = [
    (1e-13, "Sv"),
    (1e-12, "ps"),
    (1e-9, "ns"),
    (1e-6, "μs"),
    (1e-3, "ms"),
    (1, "s"),
    (60, "min"),
    (60 * 60, "hour"),
    (60 * 60 * 24, "day"),
    (60 * 60 * 24 * 7, "week"),
]


def fmt_sec(sec: float):
    size, name = 1e-13, "Sv"
    for _size, _name in time_units:
        if sec < _size:
            return f'{sec / size:.3f}{name}'
        size = _size
        name = _name
    return f'{sec / size:.3f}{name}'


def test_time(func, cb=None):
    if cb is None: return lambda _func: test_time(_func, func)

    @functools.wraps(func)
    def foo(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            cb(func, args, kwargs, time.perf_counter() - start)

    return foo


def extend_list(l: list, size: int, el=None):
    if (s := len(l)) < size:
        l.extend(el for _ in range(size - s))


def dict_find_key(d: dict, val, strict=False):
    try:
        if strict:
            return next(k for k, v in d.items() if v == val)
        else:
            return next(k for k, v in d.items() if v is val)
    except StopIteration:
        raise ValueError(val)


def try_run(try_count, exception_type=Exception, exc_cb=None):
    def dec(func):
        def wrapper(*args, **kwargs):
            _try_count = try_count
            while _try_count > 0:
                try:
                    return func(*args, **kwargs)
                except exception_type as e:
                    if _try_count <= 1:
                        raise e
                    _try_count -= 1
                    if exc_cb:
                        exc_cb(e)

        return wrapper

    return dec


def wait_until(func, timeout=-1, interval=0.1, *args, **kwargs):
    start = time.perf_counter()
    while not func(*args, **kwargs):
        if 0 < timeout < time.perf_counter() - start:
            raise TimeoutError
        time.sleep(interval)


def named_tuple_by_struct(t: typing.Type[_T], s: struct.Struct, buffer: bytearray | memoryview | bytes, offset: int = 0) -> _T:
    return t._make(s.unpack_from(buffer, offset))


def dataclass_by_struct(t: typing.Type[_T], s: struct.Struct, buffer: bytearray | memoryview | bytes, offset: int = 0) -> _T:
    return t(*s.unpack_from(buffer, offset))


def wrap_error(cb, exc_type=Exception, default_rtn=None):
    def dec(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exc_type as e:
                cb(e, *args, **kwargs)
                return default_rtn

        return wrapper

    return dec


mv_from_mem = ctypes.pythonapi.PyMemoryView_FromMemory
mv_from_mem.argtypes = (ctypes.c_void_p, ctypes.c_ssize_t, ctypes.c_int)
mv_from_mem.restype = ctypes.py_object


def callable_arg_count(func):
    return len(inspect.signature(func).parameters)


class LazyClassAttr(typing.Generic[_T]):
    def __init__(self, getter: typing.Callable[..., _T]):
        self.getter = getter
        self.owner = None
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name
        self.owner = owner

    def __get__(self, instance, owner) -> _T:
        call_arg = (instance, owner)[:callable_arg_count(self.getter)]
        setattr(self.owner, self.name, res := self.getter(*call_arg))
        return res
