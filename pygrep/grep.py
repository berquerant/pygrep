import re
from collections.abc import Callable, Iterable, Iterator
from copy import deepcopy
from dataclasses import dataclass
from threading import Event, Thread

from pygrep import queue


@dataclass
class Result:
    q: Iterable[str]
    cancel: Callable[[], None]


class BaseError(Exception):
    """Base error of pygrep."""


class InvalidThreadNumberError(BaseError):
    """Raise when specified non positive thread number."""


class InvalidRegexError(BaseError):
    """Raise when given invalid regex string."""


@dataclass
class Grep:
    regex: re.Pattern
    n: int

    @staticmethod
    def new(regex: str, n: int):
        if n < 1:
            raise InvalidThreadNumberError(n)
        try:
            return Grep(regex=re.compile(regex), n=n)
        except Exception as e:
            raise InvalidRegexError() from e

    def grep(self, src: Iterator[str]) -> Result:
        def do_grep(r: re.Pattern, req: queue.Queue[list[str]], res: queue.Queue[str]):
            for buf in req:
                for line in buf:
                    if r.search(line):
                        res.put(queue.Message(line))

        def do_read(is_cancel: Event, req: queue.Queue[list[str]]):
            buf: list[str] = []
            for line in src:
                if is_cancel.is_set():
                    return
                if len(buf) >= 100:
                    req.put(queue.Message(buf))
                    buf = []
                buf.append(line)
            if len(buf) > 0:
                req.put(queue.Message(buf))

        def launch(is_cancel: Event, threads: list[Thread],
                   req: queue.Queue[list[str]], res: queue.Queue[str]):
            try:
                do_read(is_cancel, req)
            finally:
                request_queue.put(queue.EOQ())
                for t in threads:
                    t.join()
                res.put(queue.EOQ())

        is_cancel = Event()
        request_queue: queue.Queue[list[str]] = queue.Queue.new(maxsize=self.n * 2)
        result_queue: queue.Queue[str] = queue.Queue.new(maxsize=1000)
        threads: list[Thread] = [
            Thread(
                target=do_grep,
                kwargs={
                    "r": deepcopy(self.regex),
                    "req": request_queue,
                    "res": result_queue,
                },
            ) for _ in range(self.n)
        ]
        for t in threads:
            t.start()
        Thread(
            target=launch,
            kwargs={
                "is_cancel": is_cancel,
                "threads": threads,
                "req": request_queue,
                "res": result_queue,
            },
        ).start()
        return Result(
            q=result_queue,
            cancel=is_cancel.set,
        )
