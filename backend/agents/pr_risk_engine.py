import os, re, json, requests
from typing import List, Dict, Any
from agents.impact_engine import analyze_impact, build_dependency_graph
import networkx as nx
from intelligence.contextual_risk_engine import contextual_risk_score
from dotenv import load_dotenv
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def extract_files_from_diff(diff_text: str):
    files = []
    for line in diff_text.split("\n"):
        if line.startswith("diff --git"):
            parts = line.split(" ")
            if len(parts) >= 3:
                file_path = parts[2].replace("a/", "").strip()
                # Normalize path
                file_path = file_path.lstrip("./")
                files.append(file_path)
    return list(set(files))
STRUCTURAL_WEIGHT = 0.6
SEMANTIC_WEIGHT = 0.4
def classify_final_score(score):
    if score >= 75:
        return "CRITICAL"
    elif score >= 55:
        return "HIGH"
    elif score >= 30:
        return "MODERATE"
    else:
        return "LOW"
def calculate_pr_risk(repo_path: str, changed_files: List[str]) -> Dict[str, Any]:
    impacts = analyze_impact(repo_path, changed_files)
    if not impacts:
        return {
            "pr_risk_score": 0,
            "classification": "LOW",
            "total_files_affected": 0,
            "max_impact_depth": 0,
            "high_risk_modules": [],
            "file_breakdown": [],
            "semantic_risk": {},
            "confidence_score": 0.5
        }
    graph = build_dependency_graph(repo_path)
    reverse_graph = graph.reverse(copy=False)
    total_structural_score = 0
    max_depth = 0
    all_impacted_files = set()
    high_risk_candidates = []
    for impact in impacts:
        total_structural_score += impact["risk_score"]
        max_depth = max(max_depth, impact["depth"])
        root_file = impact["file"]
        if root_file in reverse_graph:
            downstream = set(nx.descendants(reverse_graph, root_file))
            all_impacted_files.update(downstream)
            # Rank by in-degree (true centrality proxy)
            for module in downstream:
                centrality = graph.in_degree(module)
                high_risk_candidates.append((module, centrality))
    # Unique impacted files count
    total_affected = len(all_impacted_files)
    # Rank high risk modules by dependency centrality
    high_risk_candidates = sorted(
        high_risk_candidates,
        key=lambda x: x[1],
        reverse=True
    )
    high_risk_modules = [m[0] for m in high_risk_candidates[:3]]
    # Average structural score
    avg_structural = total_structural_score / len(impacts)
    # Normalize structural score relative to repo size
    repo_size = len(graph.nodes)
    structural_norm = min((total_affected / max(repo_size, 1)), 1.0)
    semantic_results = contextual_risk_score(repo_path, changed_files)
    semantic_norm = min(semantic_results["semantic_score"] / 30, 1.0)
    final_risk_score = (
        structural_norm * STRUCTURAL_WEIGHT +
        semantic_norm * SEMANTIC_WEIGHT
    ) * 100
    classification = classify_final_score(final_risk_score)
    return {
        "pr_risk_score": round(final_risk_score, 2),
        "classification": classification,
        "fusion_details": {
            "structural_score_raw": round(avg_structural, 2),
            "structural_normalized": round(structural_norm, 3),
            "semantic_score_raw": semantic_results["semantic_score"],
            "semantic_normalized": round(semantic_norm, 3),
            "weights": {
                "structural": STRUCTURAL_WEIGHT,
                "semantic": SEMANTIC_WEIGHT
            }
        },
        "total_files_affected": total_affected,
        "max_impact_depth": max_depth,
        "high_risk_modules": high_risk_modules,
        "file_breakdown": impacts,
        "semantic_risk": semantic_results,
        "confidence_score": semantic_results["confidence"]
    }
def generate_pr_ai_summary(pr_data):
    prompt = f"""
You are a senior engineering reviewer.
Given:
- PR risk score: {pr_data["pr_risk_score"]}
- Classification: {pr_data["classification"]}
- Total affected files: {pr_data["total_files_affected"]}
- Max dependency depth: {pr_data["max_impact_depth"]}
- High risk modules: {pr_data["high_risk_modules"]}
Return STRICTLY valid JSON only:
{{
  "review_focus": "...",
  "testing_strategy": "...",
  "merge_readiness": "LOW/MEDIUM/HIGH",
  "risk_explanation": "Explain in exactly 3 sentences."
}}
"""
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are a precise senior engineering reviewer that outputs valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
    )
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    content = re.sub(r"```.*?\n", "", content)  
    content = re.sub(r"```", "", content)       
    content = content.strip()
    try:
        return json.loads(content)
    except Exception as e:
        print("AI RAW RESPONSE:", content)
        return {
            "review_focus": "AI parsing failed",
            "testing_strategy": "Manual review recommended",
            "merge_readiness": "MEDIUM",
            "risk_explanation": "AI response formatting failed but PR risk engine succeeded."
        }