import time
from threading import Timer

import pytest

import pygrep.grep as grep


def test_invalid_thread_number():
    with pytest.raises(grep.InvalidThreadNumberError):
        grep.Grep.new(r"abc", 0).grep([])


def test_invalid_regex():
    with pytest.raises(grep.InvalidRegexError):
        grep.Grep.new(r"[", 1)


def test_source_error():
    class Source:
        def __init__(self):
            self.is_done = False

        def __iter__(self):
            return self

        def __next__(self):
            if self.is_done:
                raise Exception("source")
            self.is_done = True
            return "x"

    got = list(grep.Grep.new(r"x", 1).grep(Source()).q)
    assert len(got) == 0


def test_cancel():
    class Source:
        def __init__(self):
            self.i = 0

        def __iter__(self):
            return self

        def __next__(self):
            if self.i >= 10:
                raise StopIteration()
            self.i += 1
            time.sleep(0.1)
            return "x"

    r = grep.Grep.new(r".", 1).grep(Source())
    Timer(0.5, r.cancel).start()
    got = list(r.q)
    assert len(got) == 0, got


@pytest.mark.parametrize(
    "title,regex,src,n,want",
    [
        ("no input", r"match", [], 1, []),
        ("not matched", r"match", ["unreal"], 1, []),
        ("matched", r"match", ["match"], 1, ["match"]),
        ("not matched all", r"match", ["unreal"] * 200, 1, []),
        ("matched all", r"match", ["match"] * 200, 1, ["match"] * 200),
        (
            "matched partially",
            r"int",
            ["sigint", "int"] * 200,
            1,
            ["sigint", "int"] * 200,
        ),
        (
            "matched parallel",
            r"int",
            ["sigint", "int"] * 200,
            2,
            ["sigint", "int"] * 200,
        ),
    ],
)
def test_grep(title: str, regex: str, src: list[str], n: int, want: list[str]):
    got = list(grep.Grep.new(regex, n).grep(src).q)
    msg = f"{title} {got}"
    assert len(got) == len(want), msg
    assert all(x == y for x, y in zip(sorted(want), sorted(got))), msg
