import requests
import json

def download_json(id):
    project = requests.get(f"https://api.scratch.mit.edu/projects/{id}")
    token = json.loads(project.content)["project_token"]
    params = {"token": token}
    project_json = requests.get(url=f"https://projects.scratch.mit.edu/{id}", params=params)
    return(json.loads(project_json.content))

