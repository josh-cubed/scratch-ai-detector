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

args = arg_parser.parse_args()
stashed_lines: list[str] = []


def stdout_base(text: str, prefix: str = "", suffix: str = "", stash: bool = True) -> None:
    if stash:
        stashed_lines.append(text)
    else:
        print(text)

def stdout_file(text: str, prefix: str = "", suffix: str = "\n", stash: bool = True) -> None:
    if stash:
        stashed_lines.append(prefix + text + suffix)
    else:
        log_file.write(prefix + text + suffix)

def fstdout_base(text: Any, prefix: str = "", suffix: str = "", stash: bool = True) -> None:
    if stash:
        stashed_lines.append(prettyprint.format(text))
    else:
        prettyprint.prettyprint(text)

def fstdout_file(text: Any, prefix: str = "", suffix: str = "\n", stash: bool = True) -> None:
    if stash:
        stashed_lines.append(prefix + prettyprint.clean_format(text) + suffix)
    else:
        log_file.write(prefix + prettyprint.clean_format(text) + suffix)

def finish():
    for line in stashed_lines:
        stdout(line, stash=False)

    log_file.close()


stdout = stdout_base
fstdout = fstdout_base

if not args.output_logs:
    log_file = open("logs.md", "w", encoding="utf-8")
    stdout = stdout_file
    fstdout = fstdout_file