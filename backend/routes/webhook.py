from fastapi import APIRouter, Request, Header, HTTPException, BackgroundTasks
import json, tempfile, subprocess, shutil
from services.github_auth import (
    generate_installation_token,
    get_pr_files,
    post_pr_comment
)
from utils.security import verify_signature
from utils.logger import get_logger
from agents.pr_risk_engine import calculate_pr_risk, generate_pr_ai_summary
from agents.enterprise_decision_engine import build_enterprise_decision
from agents.hybrid_governance_engine import compute_hybrid_merge_decision

logger = get_logger("github-webhook")

router = APIRouter()

# ==============================
# Background Processor
# ==============================

def process_pr_event(payload: dict):
    try:
        installation_id = payload["installation"]["id"]
        repo_full_name = payload["repository"]["full_name"]
        repo_clone_url = payload["repository"]["clone_url"]
        pr_number = payload["pull_request"]["number"]

        logger.info(f"Processing PR #{pr_number} for {repo_full_name}")

        # 1️⃣ Auth
        access_token = generate_installation_token(installation_id)

        # 2️⃣ Fetch changed files
        changed_files = get_pr_files(repo_full_name, pr_number, access_token)

        # 3️⃣ Clone repo
        temp_dir = tempfile.mkdtemp()

        subprocess.run(
            ["git", "clone", "--depth", "1", repo_clone_url, temp_dir],
            check=True
        )

        try:
            # 4️⃣ Run Risk Engine
            pr_data = calculate_pr_risk(
                repo_path=temp_dir,
                changed_files=changed_files
            )

            pr_data["ai_analysis"] = generate_pr_ai_summary(pr_data)
            pr_data.update(build_enterprise_decision(pr_data))
            pr_data.update(compute_hybrid_merge_decision(pr_data))

            # 5️⃣ Format Comment
            comment_body = f"""
## 🚨 PR Governance Report

**Risk Score:** {pr_data['pr_risk_score']}
**Classification:** {pr_data['classification']}
**Final Decision:** {pr_data['hybrid_governance']['final_merge_decision']}
**Governance Level:** {pr_data['hybrid_governance']['governance_level']}

---

### 🧠 AI Analysis
{pr_data['ai_analysis']}
"""

            # 6️⃣ Post Comment
            post_pr_comment(repo_full_name, pr_number, access_token, comment_body)

            logger.info(f"PR #{pr_number} processed successfully.")

        finally:
            shutil.rmtree(temp_dir)

    except Exception as e:
        logger.error(f"Error processing PR: {str(e)}")


# ==============================
# Webhook Endpoint
# ==============================

@router.post("/github-webhook")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None)
):
    body = await request.body()

    # Verify signature
    if not verify_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=403, detail="Invalid signature")

    payload = json.loads(body)

    # Only handle PR events
    if x_github_event == "pull_request":
        action = payload.get("action")

        if action in ["opened", "reopened", "synchronize"]:
            # Add background task
            background_tasks.add_task(process_pr_event, payload)

            # Immediate response
            return {"status": "accepted"}

    return {"status": "ignored"}