import threading
import typing


class ResEvent(threading.Event):
    def __init__(self):
        super().__init__()
        self.res = None

    def set(self, data=None) -> None:
        self.res = data
        super().set()

    def wait(self, timeout: float | None = None) -> typing.Any:
        if super().wait(timeout):
            return self.res
        else:
            raise TimeoutError()


class ResEventList:
    queue: typing.List[ResEvent]

    def __init__(self):
        self.queue = [ResEvent()]
        self.lock = threading.Lock()

    def put(self, data):
        with self.lock:
            if not self.queue or self.queue[-1].is_set():
                self.queue.append(ResEvent())
            self.queue[-1].set(data)

    def get(self):
        with self.lock:
            if not self.queue:
                self.queue.append(ResEvent())
            evt = self.queue[0]
        res = evt.wait()
        with self.lock:
            if self.queue and self.queue[0] is evt:
                self.queue.pop(0)
        return res

