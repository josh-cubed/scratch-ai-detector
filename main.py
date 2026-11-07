from zipfile import ZipFile

import os
import json
import platform
import subprocess
import sys
import tests.variables as vartest
import tests.code_patterns as patterntest
import tests.coords as coordtest
import tools.projects as projects
import tools.prettyprint as prettyprint

# My code probably has some bad practices, I haven't used python in a while, sorry about that
# It's also just a prototype/proof of concept right now, I'll probably polish this later
# This script will also probably get replaced.

os_name: str = platform.system()
available_files: list[str] = list(
    filter(lambda file: file.endswith(".sb3"), os.listdir("samples"))
)
project: dict[str, list | dict] = {}

args: list[str] = sys.argv[1:]
flags: list[str] = list(filter(lambda arg: arg.startswith("--"), args))
stdout = lambda txt, prefix="", suffix="": print(txt)
fstdout = lambda txt, prefix="", suffix="": prettyprint.prettyprint(txt)

create_log_sections = "--remove-log-sections" not in flags and "--output-logs" not in flags

if "--output-logs" not in flags:
    log_file = open("logs.md", "w", encoding="utf-8")
    stdout = lambda txt, prefix="", suffix="\n": log_file.write(prefix + txt + suffix)
    fstdout = lambda txt, prefix="", suffix="\n": log_file.write(
        prefix + prettyprint.clean_format(txt) + suffix
    )


def clear() -> None:
    if os_name == "Windows":
        subprocess.run("cls", shell=True)
    else:
        subprocess.call("clear")


clear()
print("Please pick from one of the available files, or enter a project ID:")
for i, file in enumerate(available_files, start=1):
    print(f"{i}. - {file}")

answer = int(input("Enter a file number or project ID: "))
while answer <= 0:
    print("Invalid file number or project ID.")
    answer = int(input("Enter a file number or project ID: "))

if answer - 1 > len(available_files):
    print("Getting project...")
    project = projects.download_json(int(answer))
else:
    sb3file = f"samples/{available_files[answer - 1]}"

    with ZipFile(sb3file, "r") as zObject:
        zObject.extract("project.json", path="")
        zObject.close()

    with open("project.json", "r", encoding="utf-8") as project_load:
        project = json.load(project_load)

clear()

stdout("--- Begin testing ---", "# ")

stdout("Checking variables...", "\n**", "**\n")
var_results = vartest.check_variables(project, stdout, create_log_sections)

stdout("Checking script coordinates...", "\n**", "**\n\n")
coords_results = coordtest.check_script_coords(project, stdout, create_log_sections)

stdout("Checking for repetition...", "\n**", "**\n\n")
repetition_results = patterntest.analyze_repetition(project, 5)

stdout("--- Test results ---", "\n# ")
stdout("")
stdout("Variable test:", "## ")
fstdout(var_results, "```py\n", "\n```\n")

stdout("")
stdout("Coordinates test:", "## ")
fstdout(coords_results, "```py\n", "\n```\n")

stdout("")
stdout("Metadata:", "## ")
fstdout(project["meta"], "```py\n", "\n```\n")

stdout("")
stdout("Repetition test:", "## ")
stdout(patterntest.make_repetitiveness_report(repetition_results), "```\n", "\n```\n")

if "--output-logs" not in flags:
    log_file.close()
