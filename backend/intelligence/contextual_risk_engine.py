import os
from intelligence.semantic_analyzer import detect_sensitive_keywords
from intelligence.ast_parser import extract_functions
def contextual_risk_score(repo_path, changed_files):
    risk_score = 0
    reasons = []
    for file in changed_files:
        full_path = os.path.join(repo_path, file)
        if not os.path.exists(full_path):
            continue
        with open(full_path, "r", errors="ignore") as f:
            content = f.read()
        keywords = detect_sensitive_keywords(content)
        functions = extract_functions(full_path)
        if keywords:
            risk_score += len(keywords) * 5
            reasons.append(f"{file} contains sensitive keywords: {keywords}")
        if len(functions) > 10:
            risk_score += 5
            reasons.append(f"{file} has large function surface area")
    classification = "LOW"
    if risk_score > 20:
        classification = "CRITICAL"
    elif risk_score > 12:
        classification = "HIGH"
    elif risk_score > 5:
        classification = "MODERATE"
    return {
        "semantic_score": risk_score,
        "semantic_classification": classification,
        "reasoning": reasons,
        "confidence": min(0.95, 0.5 + (risk_score / 50))
    }