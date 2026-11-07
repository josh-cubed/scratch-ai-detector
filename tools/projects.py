from concurrent.futures import ThreadPoolExecutor
from zipfile import ZipFile

import requests
import json


def download_json(id):
    project = json.loads(
        requests.get(f"https://api.scratch.mit.edu/projects/{id}").content
    )
    token = project["project_token"]
    print(f"Downloading project {project["title"]}")
    params = {"token": token}
    project_json = requests.get(
        url=f"https://projects.scratch.mit.edu/{id}", params=params
    )
    return json.loads(project_json.content)


def read_assets(sb3_path):
    # All files in the ZIP that aren't project.json are assets
    with ZipFile(sb3_path, "r") as sb3:
        return {
            name: sb3.read(name) for name in sb3.namelist() if name != "project.json"
        }


def download_assets(project):
    # Fetches files from the asset server by MD5 + extension, can be used if only project.json is present
    names = {
        asset["md5ext"]
        for target in project["targets"]
        for asset in target.get("costumes", []) + target.get("sounds", [])
    }
    names = list(names)

    def fetch(name):
        response = requests.get(
            f"https://assets.scratch.mit.edu/internalapi/asset/{name}/get/"
        )
        if response.status_code == 404:
            return None  # asset isn't on the server, nothing to scan
        response.raise_for_status()
        return response.content

    # Big projects have thousands of assets, so they're downloaded concurrently for speed
    with ThreadPoolExecutor(max_workers=16) as pool:
        contents = list(pool.map(fetch, names))
    return {name: data for name, data in zip(names, contents) if data is not None}
