import os, re, json
from typing import List
from pydantic import BaseModel

from agents.dependency_agent import build_dependency_graph
from blast_radius import (
    build_reverse_graph,
    compute_blast_radius
)
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ✅ Request Model (Strong API design)
class ImpactRequest(BaseModel):
    folder_name: str
    changed_files: List[str]


BASE_REPO_DIR = "repos"


# ✅ Risk Formula (Simple > Fake Complexity)
def compute_risk_score(direct, transitive, depth):
    return (direct * 2) + (transitive * 1.5) + depth


def classify_risk(score):
    if score >= 13:
        return "HIGH"
    elif score >= 6:
        return "MEDIUM"
    return "LOW"


# ✅ Core Analyzer (ZERO duplicated logic)
def analyze_impact(folder_name, changed_files):

    repo_path = os.path.join(BASE_REPO_DIR, folder_name)

    G = build_dependency_graph(repo_path)
    reverse_graph = build_reverse_graph(G)

    results = []

    for file in changed_files:

        if file not in G:
            continue

        dependents, depth = compute_blast_radius(file, reverse_graph)

        direct = len(list(reverse_graph.successors(file)))
        transitive = len(dependents)

        score = compute_risk_score(direct, transitive, depth)
        risk = classify_risk(score)

        results.append({
            "file": file,
            "risk_score": round(score, 2),
            "risk_level": risk,
            "direct_dependents": direct,
            "transitive_dependents": transitive,
            "depth": depth
        })

    return results



def get_executive_reasoning(data):

    prompt = f"""
        You are a senior software architect.

        Analyze the risk of this code change.

        DATA:
        {data}

        Return STRICT JSON only.
        No markdown.
        No backticks.
        No explanation outside JSON.

        Format:
        {{
        "severity": "...",
        "why_risky": "...",
        "testing_recommendation": "...",
        "developer_action": "..."
        }}
        """

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    content = completion.choices[0].message.content.strip()

    # 🔥 Remove markdown fences if model adds them
    content = re.sub(r"```json|```", "", content).strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "severity": "UNKNOWN",
            "why_risky": "LLM output parsing failed",
            "testing_recommendation": "Manual review required",
            "developer_action": "Inspect raw model output"
        }