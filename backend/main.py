from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List
import subprocess, os, uuid, shutil
from agents.enterprise_decision_engine import build_enterprise_decision
from agents.hybrid_governance_engine import compute_hybrid_merge_decision
from agents.pr_risk_engine import (
    calculate_pr_risk,
    generate_pr_ai_summary
)
import hmac, hashlib, json, requests, os
from agents.github_auth import generate_app_jwt

# ==========================================================
# App Initialization
# ==========================================================

app = FastAPI(
    title="Autonomous PR Risk Engine",
    version="1.0.0",
    description="Stateless architectural impact analysis for pull requests."
)

# ==========================================================
# CORS Configuration (Adjust in production)
# ==========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to frontend domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# Request Schema
# ==========================================================

class PRRiskRequest(BaseModel):
    repo_url: HttpUrl
    changed_files: List[str]

# ==========================================================
# Health Check
# ==========================================================

@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "pr-risk-engine",
        "mode": "stateless"
    }

# ==========================================================
# PR Risk Analysis Endpoint
# ==========================================================

@app.post("/pr-risk-analysis")
def pr_risk_analysis(request: PRRiskRequest):
    temp_dir = f"/tmp/{uuid.uuid4()}"
    try:
        # 1️⃣ Shallow clone (free-tier safe)
        clone_command = [
            "git",
            "clone",
            "--depth",
            "1",
            str(request.repo_url),
            temp_dir
        ]
        result = subprocess.run(
            clone_command,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Git clone failed: {result.stderr}"
            )
        # 2️⃣ Run PR Risk Engine
        pr_data = calculate_pr_risk(
            repo_path=temp_dir,
            changed_files=request.changed_files
        )
        # 3️⃣ AI Executive Summary
        ai_summary = generate_pr_ai_summary(pr_data)
        pr_data["ai_analysis"] = ai_summary
        enterprise_layer = build_enterprise_decision(pr_data)
        pr_data.update(enterprise_layer)
        hybrid_layer = compute_hybrid_merge_decision(pr_data)
        pr_data.update(hybrid_layer)
        return pr_data
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="Repository clone timed out."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    finally:
        # 4️⃣ Always cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@app.post("/github/webhook")
async def github_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    event = request.headers.get("X-GitHub-Event")
    secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    # Verify webhook signature
    digest = "sha256=" + hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(digest, signature):
        return {"status": "invalid signature"}
    payload = json.loads(body)
    if event == "pull_request" and payload["action"] in ["opened", "synchronize"]:
        repo_clone_url = payload["repository"]["clone_url"]
        pr_number = payload["pull_request"]["number"]
        changed_files = []
        # Get installation ID
        installation_id = payload["installation"]["id"]
        # Authenticate as GitHub App
        app_jwt = generate_app_jwt()
        headers = {
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json"
        }
        # Get installation access token
        token_response = requests.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers=headers
        )
        access_token = token_response.json()["token"]
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github+json"
        }
        # Fetch changed files in PR
        files_response = requests.get(
            payload["pull_request"]["url"] + "/files",
            headers=headers
        )
        for file in files_response.json():
            changed_files.append(file["filename"])
        # Call your internal PR risk engine
        pr_data = calculate_pr_risk(
            repo_path=repo_clone_url,
            changed_files=changed_files
        )
        pr_data["ai_analysis"] = generate_pr_ai_summary(pr_data)
        pr_data.update(build_enterprise_decision(pr_data))
        pr_data.update(compute_hybrid_merge_decision(pr_data))
        # Post PR comment
        comment_body = f"""
## 🚨 PR Governance Report
**Final Decision:** {pr_data['hybrid_governance']['final_merge_decision']}
**Governance Level:** {pr_data['hybrid_governance']['governance_level']}
**Risk Score:** {pr_data['pr_risk_score']}
**Classification:** {pr_data['classification']}
"""
        requests.post(
            payload["pull_request"]["comments_url"],
            headers=headers,
            json={"body": comment_body}
        )
    return {"status": "processed"}