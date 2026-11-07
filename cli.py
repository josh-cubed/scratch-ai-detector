from typing import Any

import argparse
import tools.prettyprint as prettyprint

arg_parser = argparse.ArgumentParser(
    description="An AI-generated Scratch project detector."
)
arg_parser.add_argument(
    "--output-logs",
    action="store_true",
    help="Print the test logs to the console instead of to logs.md.",
)
arg_parser.add_argument(
    "--no-log-sections",
    action="store_true",
    help="Remove collapsible log sections in logs.md.",
)
arg_parser.add_argument(
    "--min-sequence",
    type=int,
    default=5,
    help="The minimum block count of a detectable sequence.",
)
arg_parser.add_argument(
    "--include-inits",
    action="store_true",
    help="Whether to include data initializations when testing repetition."
)

args = arg_parser.parse_args()
stashed_lines: list[str] = []


def _stdout(
    text: str,
    prefix: str = "",
    suffix: str = "",
    stash: bool = True,
    *,
    file_output: bool = False,
) -> None:
    if stash:
        stashed_lines.append(prefix + text + suffix if file_output else text)
    elif file_output:
        log_file.write(prefix + text + suffix)
    else:
        print(text)


def stdout_base(
    text: str,
    prefix: str = "",
    suffix: str = "",
    stash: bool = True,
) -> None:
    _stdout(text, prefix, suffix, stash)


def stdout_file(
    text: str,
    prefix: str = "",
    suffix: str = "\n",
    stash: bool = True,
) -> None:
    _stdout(text, prefix, suffix, stash, file_output=True)


def fstdout_base(
    text: Any,
    prefix: str = "",
    suffix: str = "",
    stash: bool = True,
) -> None:
    _stdout(prettyprint.format(text), prefix, suffix, stash)


def fstdout_file(
    text: Any,
    prefix: str = "",
    suffix: str = "\n",
    stash: bool = True,
) -> None:
    _stdout(prettyprint.clean_format(text), prefix, suffix, stash, file_output=True)


def finish() -> None:
    for line in stashed_lines:
        stdout(line, stash=False)

    log_file.close()


stdout = stdout_base
fstdout = fstdout_base

if not args.output_logs:
    log_file = open("logs.md", "w", encoding="utf-8")
    stdout = stdout_file
    fstdout = fstdout_file