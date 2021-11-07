from timeit import Timer
from pygrep import Grep


def bench_grep(n: int) -> float:
    data = ["soft", "smooth", "warm"] * 2000
    regex = r"soft|warm"

    def target():
        list(Grep.new(regex, n).grep(data).q)

    return min(Timer(target).repeat(3, 1))


for i in range(5):
    n = 1 << i
    result = bench_grep(n)
    print(f"bench_grep({n:02}): {result}")
