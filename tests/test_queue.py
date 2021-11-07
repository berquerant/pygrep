import time
from collections.abc import Callable
from threading import Thread, Timer

import pygrep.queue as queue


def timeout(interval: float, f: Callable[[], None]) -> None:
    def _raise():
        raise Exception(f"timed out ({interval} sec)")

    t = Timer(interval, _raise)
    t.start()
    f()
    t.cancel()


def test_noop():
    q = queue.Queue.new()
    timeout(1, q.wait)


def test_put():
    q = queue.Queue.new()
    q.put(queue.Message(1))
    v = q.get()
    assert v.unwrap() == 1
    q.ack()
    timeout(1, q.wait)


def test_iter():
    q = queue.Queue.new()
    for i in range(3):
        q.put(queue.Message(i))
    q.put(queue.EOQ())
    got = list(q)
    assert all(x == y for x, y in zip(range(3), got))
    timeout(1, q.wait)


def test_async():
    q = queue.Queue.new()
    got = []
    want = list(range(3))

    def consume():
        for x in q:
            got.append(x)
        timeout(1, q.wait)

    t = Thread(target=consume)
    t.start()
    for i in want:
        q.put(queue.Message(i))
    q.put(queue.EOQ())
    t.join()
    assert all(x == y for x, y in zip(want, got))


def test_async_multi():
    q = queue.Queue.new()

    def consume(data: list[int]):
        for x in q:
            time.sleep(0.01)
            data.append(x)
        timeout(1, q.wait)

    n = 4
    got = [[] for _ in range(n)]
    want = list(range(20))
    threads = [Thread(target=consume, kwargs={"data": x}) for x in got]
    for t in threads:
        t.start()

    for i in want:
        q.put(queue.Message(i))
    q.put(queue.EOQ())
    for t in threads:
        t.join()
    assert all(x == y for x, y in zip(want, sorted(sum(got, start=[]))))
