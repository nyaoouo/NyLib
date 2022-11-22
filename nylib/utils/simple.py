import threading
import pathlib


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
