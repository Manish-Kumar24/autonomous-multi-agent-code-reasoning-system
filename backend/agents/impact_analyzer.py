import os, re, json
from typing import List
from pydantic import BaseModel
from agents.dependency_agent import build_dependency_graph
from blast_radius import (
    build_reverse_graph,
    compute_blast_radius
)

def compute_risk_score(direct, transitive, depth):
    return (direct * 2) + (transitive * 1.5) + depth

def classify_risk(score):
    if score >= 20:
        return "CRITICAL"
    elif score >= 13:
        return "HIGH"
    elif score >= 6:
        return "MODERATE"
    else:
        return "LOW"

def analyze_impact(repo_path: str, changed_files: List[str]):
    print("IMPACT ANALYZER REPO PATH:", repo_path)
    print("EXISTS?", os.path.exists(repo_path))
    G = build_dependency_graph(repo_path)
    reverse_graph = build_reverse_graph(G)
    valid_files = [f for f in changed_files if f in G.nodes]
    print("GRAPH NODE SAMPLE:", list(G.nodes)[:20])
    if not valid_files:
        return [{
            "file": "INVALID_INPUT",
            "risk_score": 0,
            "risk_level": "LOW",
            "direct_dependents": 0,
            "transitive_dependents": 0,
            "depth": 0,
            "error": "Changed files do not belong to analyzed repository",
            "debug_changed_files": changed_files,
            "debug_available_files": list(G.nodes)[:10]
        }]
    changed_files = valid_files
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