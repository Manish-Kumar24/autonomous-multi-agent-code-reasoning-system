from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List
from routes.webhook import router as webhook_router
import subprocess, os, uuid, shutil, hmac, hashlib, json, requests
from agents.enterprise_decision_engine import build_enterprise_decision
from agents.hybrid_governance_engine import compute_hybrid_merge_decision
from agents.pr_risk_engine import (
    calculate_pr_risk
)
from agents.llm_review_engine import generate_llm_review
app = FastAPI(
    title="Autonomous PR Risk Engine",
    version="1.0.0",
    description="Stateless architectural impact analysis for pull requests."
)
app.include_router(webhook_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to frontend domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class PRRiskRequest(BaseModel):
    repo_url: HttpUrl
    changed_files: List[str]
@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "pr-risk-engine",
        "mode": "stateless"
    }
@app.post("/pr-risk-analysis")
def pr_risk_analysis(request: PRRiskRequest):
    temp_dir = f"/tmp/{uuid.uuid4()}"
    try:
        clone_command = ["git", "clone", "--depth", "1", str(request.repo_url), temp_dir]
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
        pr_data = calculate_pr_risk(
            repo_path=temp_dir,
            changed_files=request.changed_files
        )
        # Enterprise layer first
        enterprise_layer = build_enterprise_decision(pr_data)
        pr_data.update(enterprise_layer)
        # Hybrid governance next
        hybrid_layer = compute_hybrid_merge_decision(pr_data)
        pr_data.update(hybrid_layer)
        # LLM interpretation layer last
        ai_summary = generate_llm_review(pr_data)
        pr_data["ai_analysis"] = ai_summary
        # Deterministic override protection
        if pr_data["hybrid_governance"]["governance_level"] == "CRITICAL":
            pr_data["ai_analysis"]["merge_readiness"] = "LOW"
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
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)