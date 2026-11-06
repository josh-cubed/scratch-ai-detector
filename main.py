from zipfile import ZipFile
import os
import subprocess
import json
import tests.variables as vartest
import tools.projects as projects

# My code probably has some bad practices, I haven't used python in a while, sorry about that
# It's also just a prototype/proof of concept right now, I'll probably polish this later
# This script will also probably get replaced.

subprocess.call("clear")

available_files = []
project = []

for i in os.listdir("samples"):
    if i.endswith(".sb3"):
        available_files.append(i)

print("Please pick from one of the available files, or enter a project ID:")
for i in range(0, len(available_files)):
    print(str(i+1)+". - " + available_files[i])


answer = int(input("Enter a file number or project ID: "))
if int(answer)-1 > len(available_files):
    project = projects.download_json(int(answer))
    print(project)
else:
    sb3file = "samples/"+available_files[answer - 1]

    with ZipFile(sb3file, 'r') as zObject:
        # Extracting specific file in the zip
        # into a specific location.
        zObject.extract(
            "project.json", path="")
        zObject.close()

    with open("project.json", "r") as project_load:
        data=project_load.read()
        project = json.loads(data)

subprocess.call("clear")

print("Checking variables...")

var_results = vartest.check_variables(project)

print("Checking script coordinates...")

coords_results = vartest.check_script_coords(project)

# subprocess.call("clear")

print("--- Test results ---")
print("Variable test:")
print(var_results)

print("Coordinates test:")
print(coords_results)
