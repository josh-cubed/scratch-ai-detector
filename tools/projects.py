import requests
import json

def download_json(id):
    project = json.loads(requests.get(f"https://api.scratch.mit.edu/projects/{id}").content)
    token = project["project_token"]
    print(f"Downloading project {project["title"]}")
    params = {"token": token}
    project_json = requests.get(url=f"https://projects.scratch.mit.edu/{id}", params=params)
    return(json.loads(project_json.content))

