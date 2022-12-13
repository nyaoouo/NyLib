import functools
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

