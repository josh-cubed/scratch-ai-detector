from cli import args, finish, fstdout, stdout
from zipfile import ZipFile

import json
import os
import platform
import subprocess
import tests.variables as vartest
import tests.code_patterns as patterntest
import tests.coords as coordtest
import tools.projects as projects
import tools.prettyprint as prettyprint

# My code probably has some bad practices, I haven't used python in a while, sorry about that
# It's also just a prototype/proof of concept right now, I'll probably polish this later
# This script will also probably get replaced.

os_name: str = platform.system()
available_files: list[str] = []
project: dict[str, list | dict] = {}
create_log_sections = not args.no_log_sections and not args.output_logs


for category in ("human", "ai"):
    category_dir = os.path.join("samples", category)
    if os.path.isdir(category_dir):
        for file in sorted(os.listdir(category_dir)):
            if file.endswith(".sb3"):
                available_files.append(f"{category}/{file}")


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

if answer > len(available_files):
    if not args.output_logs:
        stdout(f"https://scratch.mit.edu/projects/{answer}", stash=False)
    print("Getting project...")
    project = projects.download_json(int(answer))
else:
    sb3file = os.path.join("samples", available_files[answer - 1])
    if not args.output_logs:
        stdout(f"{sb3file}", stash=False)

    with ZipFile(sb3file, "r") as zObject:
        zObject.extract("project.json", path="")
        zObject.close()

    with open("project.json", "r", encoding="utf-8") as project_load:
        project = json.load(project_load)

clear()

stdout("--- Test Logs ---", "# ")

stdout("Checking variables...", "\n**", "**\n\n")
var_results = vartest.check_variables(project, stdout, create_log_sections)

stdout("Checking script coordinates...", "\n**", "**\n\n")
coords_results = coordtest.check_script_coords(project, stdout, create_log_sections)

stdout("Checking for repetition...", "\n**", "**\n\n")
repetition_results = patterntest.analyze_repetition(
    project, args.min_sequence, not args.include_inits
)

stdout("Checking for default input residues...", "\n**", "**\n\n")
residue_results = patterntest.analyze_default_input_values(project)

stdout("--- Test Results ---", "\n# ", stash=False)
stdout("", stash=False)
stdout("Variable:", "## ", stash=False)
fstdout(var_results, "```py\n", "\n```\n", stash=False)

stdout("", stash=False)
stdout("Coordinates:", "## ", stash=False)
fstdout(coords_results, "```py\n", "\n```\n", stash=False)

stdout("", stash=False)
stdout("Metadata:", "## ", stash=False)
fstdout(project["meta"], "```py\n", "\n```\n", stash=False)

stdout("", stash=False)
stdout("Repetition:", "## ", stash=False)
stdout(
    patterntest.make_repetition_report(repetition_results),
    "```\n",
    "\n```\n",
    stash=False,
)

stdout("", stash=False)
stdout("Default input residue:", "## ", stash=False)
stdout(
    patterntest.make_default_input_values_report(residue_results),
    "```\n",
    "\n```\n",
    stash=False,
)

# Cleanup file after use (VERY IMPORTANT, DO NOT REMOVE)
if not args.output_logs:
    finish()
