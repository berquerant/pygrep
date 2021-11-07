import queue
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from threading import Semaphore
from typing import Protocol, TypeVar, cast

U = TypeVar("U", covariant=True)


class MessageProto(Protocol[U]):
    """A queue message protocol."""

    def unwrap(self) -> U:
        """Return the contained value."""

    def eoq(self) -> bool:
        """Return True if End Of Queue."""


class UnwrapEOQError(Exception):
    """Exception raised when unwrap `EOQ`."""


class EOQ(MessageProto[U]):
    """A queue message indicates the end of the queue."""

    def eoq(self) -> bool:
        return True

    def unwrap(self) -> U:
        raise UnwrapEOQError()


class Message(MessageProto[U]):
    """A queue message."""

    def __init__(self, value: U):
        self.value = value

    def eoq(self) -> bool:
        return False

    def unwrap(self) -> U:
        return self.value


T = TypeVar("T")


class QueueProto(Protocol[T]):
    """A queue protocol."""

    def get(self) -> MessageProto[T]:
        """Remove a message from the queue and return it."""

    def put(self, msg: MessageProto[T]) -> None:
        """Put a message to the queue."""

    def ack(self) -> None:
        """Notify the queue of successful consumption."""

    def wait(self) -> None:
        """Wait until all messages are consumed."""


@dataclass
class QueueIterState:
    """A state of queue iterator.
    is_eoq becomes True when got `EOQ`."""

    sem: Semaphore
    is_eoq: bool


@dataclass
class QueueIter(Iterator[T]):
    q: QueueProto
    state: QueueIterState

    def __iter__(self) -> Iterator[T]:
        return self

    def __next__(self) -> T:
        with self.state.sem:
            if self.state.is_eoq:
                raise StopIteration()
            v = self.q.get()
            self.q.ack()
            if v.eoq():
                self.state.is_eoq = True
                raise StopIteration()
            return v.unwrap()


class Queue(QueueProto, Iterable[T]):
    def __init__(self, q: queue.Queue):
        self.q = q
        self.iter_state = QueueIterState(
            sem=Semaphore(),
            is_eoq=False,
        )

    @staticmethod
    def new(maxsize=0):
        return Queue(q=queue.Queue(maxsize=maxsize))

    def get(self) -> MessageProto[T]:
        return cast(MessageProto[T], self.q.get())

    def put(self, msg: MessageProto[T]) -> None:
        self.q.put(msg)

    def ack(self) -> None:
        self.q.task_done()

    def wait(self) -> None:
        self.q.join()

    def __iter__(self) -> Iterator[T]:
        return QueueIter(q=self, state=self.iter_state)
