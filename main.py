from zipfile import ZipFile

import os
import json
import platform
import subprocess
import tests.variables as vartest
import tools.projects as projects

# My code probably has some bad practices, I haven't used python in a while, sorry about that
# It's also just a prototype/proof of concept right now, I'll probably polish this later
# This script will also probably get replaced.

os_name: str = platform.system()
available_files: list[str] = list(
    filter(lambda file: file.endswith(".sb3"), os.listdir("samples"))
)
project: dict[str, list | dict] = {}


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

if answer-1 > len(available_files):
    print("Getting project...")
    project = projects.download_json(int(answer))
    #print(project)
else:
    sb3file = f"samples/{available_files[answer - 1]}"

    with ZipFile(sb3file, "r") as zObject:
        zObject.extract("project.json", path="")
        zObject.close()

    with open("project.json", "r") as project_load:
        project = json.load(project_load)

clear()

print("Checking variables...")
var_results = vartest.check_variables(project)

print("Checking script coordinates...")
coords_results = vartest.check_script_coords(project)

print("\n--- Test results ---")
print("\nVariable test:")
print(var_results)

print("\nCoordinates test:")
print(coords_results)

print("\nMetadata:")
print(project["meta"])
