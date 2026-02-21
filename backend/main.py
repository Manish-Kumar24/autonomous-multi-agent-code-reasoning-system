from pydantic import BaseModel
from typing import Optional, List
import os, uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from repo_loader import clone_repo
from repo_scanner import scan_repository
from agents.stack_detector import detect_stack
from agents.repo_summarizer import summarize_repo, file_explainer_agent
from agents.dependency_agent import dependency_agent, build_dependency_graph
from agents.repo_metrics_analyzer import analyze_repository
from agents.repo_risk_engine import compute_repo_risk_score
from agents.repo_executive_agent import generate_repo_executive_summary
from agents.pr_risk_engine import calculate_pr_risk, generate_pr_ai_summary, extract_files_from_diff
from fastapi import Body
from blast_radius import (
    build_reverse_graph,
    compute_blast_radius,
    calculate_criticality,
    generate_reason,
    calculate_severity
)
from agents.impact_analyzer import (
    ImpactRequest,
    analyze_impact,
    get_executive_reasoning
)

app = FastAPI()
print("PORT ENV:", os.environ.get("PORT"))

# === CORS configuration ===
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",  # ADD THIS
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.join(BASE_DIR, "repos")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # allow both localhost and 127.0.0.1
    allow_credentials=True,
    allow_methods=["*"],         # GET, POST, OPTIONS, etc.
    allow_headers=["*"],
)

class RepoRequest(BaseModel):
    repo_url: str
    folder_name: str

@app.get("/")
async def root():
    return {"message": "Backend is running"}

@app.post("/clone-repo")
async def clone_repo_endpoint(req: RepoRequest):
    try:
        path = clone_repo(req.repo_url, req.folder_name)
        return {"message": f"Repo cloned at {path}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/scan-repo")
def scan_repo(folder_name: str):
    repo_path = os.path.join(REPO_DIR, folder_name)
    if not os.path.exists(repo_path):
        return {"error": "Repo not found"}
    files = scan_repository(repo_path)
    return {
        "total_files": len(files),
        "files": files[:50]
    }

@app.get("/detect-stack")
def stack(folder_name: str):
    repo_path = os.path.join(REPO_DIR, folder_name)
    if not os.path.exists(repo_path):
        return {"error": "Repo not found"}
    result = detect_stack(repo_path)
    return result

@app.get("/summarize-repo")
def summarize(folder_name: str):
    repo_path = f"repos/{folder_name}"
    if not os.path.exists(repo_path):
        return {"error": "Repo not found"}
    return summarize_repo(repo_path)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_REPO_DIR = os.path.join(BASE_DIR, "repos")

@app.get("/explain-file")
async def explain_file(path: str = Query(...)):
    if not path.startswith(BASE_REPO_DIR):
        return {"error": "Invalid file path"}
    try:
        with open(path, "r", errors="ignore") as f:
            lines = f.readlines()
        # ⭐ Elite reading strategy
        if len(lines) > 400:
            content = "".join(lines[:300] + ["\n...\n"] + lines[-100:])
        else:
            content = "".join(lines)
        explanation = file_explainer_agent(content)
        return {
            "explanation": explanation,
            "error": False
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/dependency-graph")
def dependency_graph(folder_name: str):
    repo_path = f"repos/{folder_name}"
    if not os.path.exists(repo_path):
        return {"error": "Repository not found"}
    result = dependency_agent(repo_path)
    return result

@app.get("/architecture/blast-radius")
def blast_radius(folder_name: str, file: str):
    repo_path = f"repos/{folder_name}"
    G = build_dependency_graph(repo_path)
    if file not in G:
        return {"error": "File not found in repository"}
    reverse_graph = build_reverse_graph(G)
    # ✅ Safety check
    if file not in reverse_graph:
        return {
            "error": f"{file} not found in repository graph"
        }
    dependents, max_depth = compute_blast_radius(file, reverse_graph)
    score, risk = calculate_criticality(len(dependents), max_depth)
    severity = calculate_severity(score, max_depth)
    direct_dependents = len(list(reverse_graph.successors(file)))
    reason = generate_reason(
    file=file,
    direct=direct_dependents,
    transitive=len(dependents),
    depth=max_depth,
    risk=risk
)
    return {
        "file": file,
        "severity": severity,
        "risk_level": risk,
        "reason": reason,
        # "direct_dependents": direct_dependents,
        "direct_dependents": direct_dependents,
        "transitive_dependents": len(dependents),
        "max_impact_depth": max_depth,
        "criticality_score": round(score, 2)
    }

@app.post("/impact-analysis")
def impact_analysis(req: ImpactRequest):
    results = analyze_impact(req.folder_name, req.changed_files)
    if not results:
        return {"error": "No valid files found in repository"}
    reasoning = get_executive_reasoning(results)
    return {
        "analysis": results,
        "executive_summary": reasoning
    }

@app.get("/repo-risk-score")
async def get_repo_risk_score(folder_name: str):
    repo_path = os.path.join(REPO_DIR, folder_name)
    if not os.path.exists(repo_path):
        return {"error": "Repository not found"}
    graph = build_dependency_graph(repo_path)
    metrics = analyze_repository(graph)  # your existing function
    risk_data = compute_repo_risk_score(
        architecture_health=metrics["architecture_health"],
        max_dependency_depth=metrics["max_dependency_depth"],
        cycle_count=metrics["cycle_count"],
        avg_dependents=metrics["avg_dependents"],
        high_impact_file_count=metrics["high_impact_file_count"],
        impact_scores_average=metrics["impact_scores_average"],
    )
    executive_layer = generate_repo_executive_summary(metrics, risk_data)
    return {
        **risk_data,
        "executive_analysis": executive_layer
    }

class PRRiskRequest(BaseModel):
    folder_name: str
    changed_files: Optional[List[str]] = None
    git_diff: Optional[str] = None

def generate_reviewer_suggestion(pr_data):
    classification = pr_data.get("classification", "LOW")
    affected = pr_data.get("total_files_affected", 0)
    depth = pr_data.get("max_impact_depth", 0)
    high_risk_modules = pr_data.get("high_risk_modules", [])
    if classification == "CRITICAL":
        return {
            "primary_reviewer": "Senior Architect",
            "secondary_reviewer": "Security Lead",
            "approvals_required": 2,
            "architecture_review": True,
            "security_review": True,
            "reason": "Critical architectural impact with deep dependency propagation"
        }
    elif classification == "HIGH":
        return {
            "primary_reviewer": "Senior Maintainer",
            "secondary_reviewer": "Module Owner",
            "approvals_required": 2,
            "architecture_review": depth >= 3,
            "security_review": affected >= 5,
            "reason": "High downstream impact affecting core modules"
        }
    elif classification == "MODERATE":
        return {
            "primary_reviewer": "Module Owner",
            "secondary_reviewer": None,
            "approvals_required": 1,
            "architecture_review": False,
            "security_review": False,
            "reason": "Moderate impact limited to direct dependencies"
        }
    else:
        return {
            "primary_reviewer": "Peer Developer",
            "secondary_reviewer": None,
            "approvals_required": 1,
            "architecture_review": False,
            "security_review": False,
            "reason": "Low impact change with no significant downstream effects"
        }

def calculate_confidence_metric(pr_data):
    classification = pr_data.get("classification", "LOW")
    depth = pr_data.get("max_impact_depth", 0)
    affected = pr_data.get("total_files_affected", 0)
    score = pr_data.get("pr_risk_score", 0)
    confidence = 50  # base confidence
    # Depth increases confidence
    confidence += min(depth * 5, 20)
    # More affected files increases confidence
    confidence += min(affected * 2, 20)
    # Higher risk score increases confidence
    confidence += min(score, 20)
    # Classification weight
    if classification in ["HIGH", "CRITICAL"]:
        confidence += 10
    confidence = min(round(confidence, 2), 100)
    # Confidence level bucket
    if confidence >= 85:
        level = "VERY HIGH"
    elif confidence >= 70:
        level = "HIGH"
    elif confidence >= 50:
        level = "MEDIUM"
    else:
        level = "LOW"
    return {
        "confidence_score": confidence,
        "confidence_level": level
    }

def generate_merge_decision(pr_data, confidence_data):
    classification = pr_data.get("classification", "LOW")
    confidence_score = confidence_data.get("confidence_score", 0)
    if classification == "CRITICAL":
        decision = "BLOCK"
        reason = "Critical architectural risk detected."
    elif classification == "HIGH":
        if confidence_score >= 70:
            decision = "BLOCK"
            reason = "High risk with strong confidence in impact propagation."
        else:
            decision = "MANUAL_REVIEW"
            reason = "High risk but confidence is moderate."
    elif classification == "MODERATE":
        if confidence_score >= 75:
            decision = "MANUAL_REVIEW"
            reason = "Moderate risk with significant downstream signals."
        else:
            decision = "ALLOW_WITH_REVIEW"
            reason = "Moderate impact with limited confidence."
    else:
        decision = "AUTO_APPROVE"
        reason = "Low impact change."
    return {
        "merge_decision": decision,
        "decision_reason": reason
    }

def generate_testing_recommendation(pr_data):
    classification = pr_data.get("classification", "LOW")
    depth = pr_data.get("max_impact_depth", 0)
    affected = pr_data.get("total_files_affected", 0)
    if classification == "CRITICAL":
        return {
            "unit_testing": "Mandatory for all changed modules",
            "integration_testing": "Required across impacted dependency chain",
            "regression_testing": "Full regression suite execution required",
            "performance_testing": "Recommended",
            "security_testing": "Required",
            "test_coverage_target": ">= 85%"
        }
    elif classification == "HIGH":
        return {
            "unit_testing": "Mandatory for changed and directly impacted modules",
            "integration_testing": "Required for affected downstream modules",
            "regression_testing": "Core regression suite required",
            "performance_testing": "Optional but recommended",
            "security_testing": "If core modules impacted",
            "test_coverage_target": ">= 75%"
        }
    elif classification == "MODERATE":
        return {
            "unit_testing": "Required for changed modules",
            "integration_testing": "Recommended for direct dependents",
            "regression_testing": "Targeted regression tests",
            "performance_testing": "Not required",
            "security_testing": "Not required",
            "test_coverage_target": ">= 60%"
        }
    else:
        return {
            "unit_testing": "Basic validation testing",
            "integration_testing": "Not required",
            "regression_testing": "Smoke tests sufficient",
            "performance_testing": "Not required",
            "security_testing": "Not required",
            "test_coverage_target": ">= 50%"
        }

@app.post("/pr-risk-analysis")
def pr_risk_analysis(request: PRRiskRequest):
    if request.git_diff:
        changed_files = extract_files_from_diff(request.git_diff)
    else:
        changed_files = request.changed_files or []
    repo_path = f"repos/{request.folder_name}"
    graph = build_dependency_graph(repo_path)
    print("GRAPH KEYS SAMPLE:", list(graph.nodes())[:20])
    print("CHANGED FILES:", changed_files)
    pr_data = calculate_pr_risk(request.folder_name, changed_files)
    # ✅ Generate reviewer suggestion
    reviewer_suggestion = generate_reviewer_suggestion(pr_data)
    pr_data["reviewer_suggestion"] = reviewer_suggestion
    # NEW: Structured testing recommendation
    testing_recommendation = generate_testing_recommendation(pr_data)
    pr_data["testing_recommendation"] = testing_recommendation
    # ✅ AI Summary
    ai_summary = generate_pr_ai_summary(pr_data)
    pr_data["ai_analysis"] = ai_summary
    # ✅ Confidence Metric
    confidence_data = calculate_confidence_metric(pr_data)
    pr_data["confidence"] = confidence_data
    # ✅ Merge Decision Logic
    merge_decision = generate_merge_decision(pr_data, confidence_data)
    pr_data["merge_control"] = merge_decision
    return pr_data