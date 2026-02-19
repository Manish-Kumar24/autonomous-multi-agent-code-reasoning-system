import os, re, json, requests
from typing import List, Dict, Any
from agents.impact_analyzer import analyze_impact  
import networkx as nx
from agents.dependency_agent import build_dependency_graph
from collections import Counter
from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def extract_files_from_diff(diff_text: str):
    files = []
    for line in diff_text.split("\n"):
        if line.startswith("diff --git"):
            parts = line.split(" ")
            if len(parts) >= 3:
                file_path = parts[2].replace("a/", "").strip()
                # Normalize path
                file_path = file_path.replace("backend/", "")
                file_path = file_path.lstrip("./")
                files.append(file_path)
    return list(set(files))

def classify_pr_risk(avg_score: float, impacts: list, max_depth: int) -> str:
    # 1️⃣ If any file is CRITICAL → PR CRITICAL
    if any(impact["risk_level"] == "CRITICAL" for impact in impacts):
        return "CRITICAL"
    # 2️⃣ If any file is HIGH and dependency depth is significant → PR HIGH
    if any(impact["risk_level"] == "HIGH" for impact in impacts) and max_depth >= 3:
        return "HIGH"
    # 3️⃣ Fallback to aggregated score thresholds
    if avg_score >= 75:
        return "CRITICAL"
    elif avg_score >= 50:
        return "HIGH"
    elif avg_score >= 25:
        return "MODERATE"
    else:
        return "LOW"

def calculate_pr_risk(folder_name: str, changed_files: List[str]) -> Dict[str, Any]:
    # Call analyze_impact once with full list
    impacts = analyze_impact(folder_name, changed_files)
    # Build dependency graph once
    repo_path = os.path.join("repos", folder_name)
    print("PR ENGINE REPO PATH:", repo_path)
    graph = build_dependency_graph(repo_path)
    # Reverse graph to get dependents (who depends on changed file)
    reverse_graph = graph.reverse(copy=False)
    all_downstream_modules = []
    if not impacts:
        return {
            "pr_risk_score": 0,
            "classification": "LOW",
            "total_files_affected": 0,
            "max_impact_depth": 0,
            "high_risk_modules": [],
            "file_breakdown": []
        }
    total_score = 0
    total_affected = 0
    max_depth = 0
    high_risk_modules = []
    for impact in impacts:
        score = impact["risk_score"]
        depth = impact["depth"]
        direct = impact["direct_dependents"]
        transitive = impact["transitive_dependents"]
        total_score += score
        total_affected += direct + transitive
        max_depth = max(max_depth, depth)
        file_name = impact["file"]
        # Collect downstream modules (blast radius)
        if file_name in reverse_graph:
            downstream = list(nx.descendants(reverse_graph, file_name))
            all_downstream_modules.extend(downstream)
        
    # 🔥 SMART DOWNSTREAM IMPACT RANKING
    unique_downstream = list(set(all_downstream_modules))
    scored_modules = []
    for module in unique_downstream:
        try:
            # Count how many modules depend on this module
            module_dependents = nx.descendants(reverse_graph, module)
            dependent_count = len(module_dependents)
            # Calculate max depth from this module
            max_depth_module = 0
            for target in module_dependents:
                try:
                    depth = nx.shortest_path_length(reverse_graph, module, target)
                    max_depth_module = max(max_depth_module, depth)
                except:
                    pass
            impact_score = (dependent_count * 2) + max_depth_module
            scored_modules.append({
                "module": module,
                "impact_score": impact_score,
                "dependents": dependent_count,
                "depth": max_depth_module
            })
        except:
            pass
    # Sort by impact score descending
    scored_modules = sorted(
        scored_modules,
        key=lambda x: x["impact_score"],
        reverse=True
    )
    # Return top 3 modules
    high_risk_modules = [m["module"] for m in scored_modules[:3]]

    avg_score = total_score / len(impacts)
    classification = classify_pr_risk(avg_score, impacts, max_depth)
    return {
        "pr_risk_score": round(avg_score, 2),
        "classification": classification,
        "total_files_affected": total_affected,
        "max_impact_depth": max_depth,
        "high_risk_modules": high_risk_modules,
        "file_breakdown": impacts
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

    # 🔥 Robust Markdown Removal
    content = re.sub(r"```.*?\n", "", content)  # remove opening ```
    content = re.sub(r"```", "", content)       # remove closing ```
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