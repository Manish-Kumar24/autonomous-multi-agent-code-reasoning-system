import os
import git

BASE_DIR = os.path.join(os.getcwd(), "repos")
os.makedirs(BASE_DIR, exist_ok=True)

def clone_repo(repo_url: str, folder_name: str):
    dest_path = os.path.join(BASE_DIR, folder_name)
    if os.path.exists(dest_path):
        raise Exception(f"Folder '{folder_name}' already exists!")
    git.Repo.clone_from(repo_url, dest_path)
    return dest_path
