import os
import jwt
import time
import requests
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_PRIVATE_KEY = os.getenv("GITHUB_PRIVATE_KEY")
def generate_jwt():
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + 600,
        "iss": GITHUB_APP_ID
    }
    encoded_jwt = jwt.encode(
        payload,
        GITHUB_PRIVATE_KEY,
        algorithm="RS256"
    )
    return encoded_jwt
def generate_installation_token(installation_id: int):
    jwt_token = generate_jwt()
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json"
    }
    response = requests.post(
        f"https://api.github.com/app/installations/{installation_id}/access_tokens",
        headers=headers
    )
    response.raise_for_status()
    return response.json()["token"]

def get_pr_files(repo_full_name: str, pr_number: int, access_token: str):
    # 1️⃣ Get changed file names
    files_url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/files"
    headers_json = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github+json"
    }
    response = requests.get(files_url, headers=headers_json)
    response.raise_for_status()
    files = response.json()
    changed_files = [file["filename"] for file in files]
    # 2️⃣ Get FULL unified diff (CRITICAL FIX)
    diff_url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}"
    headers_diff = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3.diff"
    }
    diff_response = requests.get(diff_url, headers=headers_diff)
    diff_response.raise_for_status()
    diff_text = diff_response.text
    return {
        "changed_files": changed_files,
        "diff_text": diff_text
    }

def post_pr_comment(repo_full_name: str, pr_number: int, access_token: str, body: str):
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github+json"
    }
    response = requests.post(url, headers=headers, json={"body": body})
    response.raise_for_status()