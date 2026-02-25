import requests

def get_pr_files(repo_full_name: str, pr_number: int, access_token: str):
    url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/files"

    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    files = response.json()
    return [file["filename"] for file in files]


def post_pr_comment(repo_full_name: str, pr_number: int, access_token: str, body: str):
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"

    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.post(url, headers=headers, json={"body": body})
    response.raise_for_status()