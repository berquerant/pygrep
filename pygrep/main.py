import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from pygrep import Grep


def grep_stdin(g: Grep):
    r = g.grep((x.rstrip() for x in sys.stdin))
    for line in r.q:
        print(line)


def grep_file(g: Grep, filename: str):
    with open(filename) as f:
        r = g.grep((x.rstrip() for x in f))
        for line in r.q:
            print(line)


def grep_files(g: Grep, filenames: list[str]):
    for filename in filenames:
        with open(filename) as f:
            r = g.grep((x.rstrip() for x in f))
            for line in r.q:
                print(f"{filename}:{line}")


def execute(regex: str, n: int, files: list[str]):
    g = Grep.new(regex, n)
    match len(files):
        case 0:
            grep_stdin(g)
        case 1:
            grep_file(g, files[0])
        case _:
            grep_files(g, files)


def main():
    parser = ArgumentParser(
        "pygrep",
        formatter_class=RawDescriptionHelpFormatter,
        epilog="""cat file | pygrep [flags] REGEX
pygrep [flags] REGEX files...

Note:
The matched lines are not guaranteed to be in order in which they appear in the input.""",
    )
    parser.add_argument("-j", type=int, action="store", default=1, help="thread num")
    parser.add_argument("regex", metavar="REGEX", type=str, nargs=1, help="regex")
    parser.add_argument("files", metavar="FILE", type=str, nargs="*", help="file")
    args = parser.parse_args()
    execute(**{
        "regex": args.regex[0],
        "n": args.j,
        "files": args.files,
    })


if __name__ == "__main__":
    main()
