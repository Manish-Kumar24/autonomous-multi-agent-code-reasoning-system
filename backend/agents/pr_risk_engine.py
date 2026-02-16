import os, re, json, requests
from typing import List, Dict, Any
from agents.impact_analyzer import analyze_impact  # adjust import if needed
from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def extract_files_from_diff(git_diff: str) -> List[str]:
    changed_files = set()
    for line in git_diff.split("\n"):
        if line.startswith("diff --git"):
            parts = line.split(" ")
            if len(parts) >= 3:
                file_path = parts[2]  # a/path/to/file
                if file_path.startswith("a/"):
                    file_path = file_path[2:]
                changed_files.add(file_path)

    return list(changed_files)

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

        if impact["risk_level"] in ["HIGH", "CRITICAL"]:
            high_risk_modules.append(impact["file"])

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