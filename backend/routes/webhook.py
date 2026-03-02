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
import textwrap
logger = get_logger("github-webhook")
router = APIRouter()

def process_pr_event(payload: dict):
    try:
        installation_id = payload["installation"]["id"]
        repo_full_name = payload["repository"]["full_name"]
        repo_clone_url = payload["repository"]["clone_url"]
        pr_number = payload["pull_request"]["number"]
        changed_files_count = payload["pull_request"].get("changed_files", 0)
        logger.info(f"Processing PR #{pr_number} for {repo_full_name}")

        access_token = generate_installation_token(installation_id)
        pr_files_data = get_pr_files(repo_full_name, pr_number, access_token)
        changed_files = pr_files_data["changed_files"]
        diff_text = pr_files_data["diff_text"]
        temp_dir = tempfile.mkdtemp()
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch",
             payload["pull_request"]["head"]["ref"],
             repo_clone_url, temp_dir],
            check=True
        )
        try:
            pr_data = calculate_pr_risk(
                repo_path=temp_dir,
                changed_files=changed_files, 
                diff_text=diff_text
            )
            pr_data["ai_analysis"] = generate_pr_ai_summary(pr_data)
            pr_data.update(build_enterprise_decision(pr_data))
            pr_data.update(compute_hybrid_merge_decision(pr_data))
            # Format high risk modules as bullet list
            clean_modules = []
            for module in pr_data["high_risk_modules"]:
                # Split in case newline slipped inside
                parts = module.splitlines()
                for p in parts:
                    p = p.strip()
                    if p:
                        clean_modules.append(p)
            high_risk_modules_list = [f"- `{m}`" for m in clean_modules]
            high_risk_modules = "\n".join(high_risk_modules_list)
            # Sanitize AI output to preserve __init__.py formatting
            review_focus = pr_data["ai_analysis"]["review_focus"]
            testing_strategy = pr_data["ai_analysis"]["testing_strategy"]
            risk_explanation = pr_data["ai_analysis"]["risk_explanation"]
            for module in pr_data["high_risk_modules"]:
                review_focus = review_focus.replace(module, f"`{module}`")
                testing_strategy = testing_strategy.replace(module, f"`{module}`")
                risk_explanation = risk_explanation.replace(module, f"`{module}`")
            print(diff_text[:300])
            # 🔥 THIS IS THE ONLY REAL FIX
            comment_body = f"""## 🚨 PR Governance Report

**Risk Score:** {pr_data['pr_risk_score']}  
**Classification:** {pr_data['classification']}  
**Final Decision:** {pr_data['hybrid_governance']['final_merge_decision']}  
**Governance Level:** {pr_data['hybrid_governance']['governance_level']}  

---

### 📊 Impact Summary
- **Total Files Affected:** {pr_data['total_files_affected']}
- **Max Dependency Depth:** {pr_data['max_impact_depth']}
- **Security Flags Detected:** {"YES" if pr_data.get("security_flag") else "NO"}

**High Risk Modules:**

{high_risk_modules}

---

### 🧠 AI Analysis

**Review Focus:**  
{review_focus}

**Testing Strategy:**  
{testing_strategy}

**Merge Readiness:**  
{pr_data['ai_analysis']['merge_readiness']}

**Risk Explanation:**  
{risk_explanation}
""".strip()
            post_pr_comment(repo_full_name, pr_number, access_token, comment_body)
            logger.info(f"PR #{pr_number} processed successfully.")
            print("COMMENT LENGTH:", len(comment_body))
        finally:
            shutil.rmtree(temp_dir)
    except Exception as e:
        logger.exception("Error processing PR")

@router.post("/github-webhook")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None)
):
    body = await request.body()
    if not verify_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=403, detail="Invalid signature")
    payload = json.loads(body)
    if x_github_event == "pull_request":
        action = payload.get("action")
        if action in ["opened", "reopened", "synchronize"]:
            background_tasks.add_task(process_pr_event, payload)
            return {"status": "accepted"}
    return {"status": "ignored"}