def compute_hybrid_merge_decision(pr_data: dict) -> dict:
    """
    Hybrid Governance Engine
    Combines deterministic risk scoring + AI signal + depth impact
    to produce final merge authority decision.
    """

    risk_score = pr_data.get("pr_risk_score", 0)
    classification = pr_data.get("classification", "LOW")
    depth = pr_data.get("max_impact_depth", 0)

    ai_data = pr_data.get("ai_analysis", {})
    ai_merge_signal = ai_data.get("merge_readiness", "MEDIUM")

    # -----------------------------------
    # Weighted Governance Score
    # -----------------------------------

    governance_score = 0

    # Risk weight (0–50)
    governance_score += min(50, risk_score * 3)

    # Depth weight (0–30)
    governance_score += min(30, depth * 10)

    # AI signal weight (0–20)
    if ai_merge_signal == "LOW":
        governance_score += 20
    elif ai_merge_signal == "MEDIUM":
        governance_score += 10
    else:
        governance_score += 0

    # -----------------------------------
    # Final Merge Decision
    # -----------------------------------

    if governance_score >= 70:
        final_decision = "BLOCK"
        level = "CRITICAL"
    elif governance_score >= 40:
        final_decision = "REVIEW_REQUIRED"
        level = "MODERATE"
    else:
        final_decision = "ALLOW"
        level = "SAFE"

    hybrid_result = {
        "hybrid_governance": {
            "governance_score": round(governance_score, 2),
            "governance_level": level,
            "final_merge_decision": final_decision,
            "explanation": "Decision derived from weighted risk score, dependency depth, and AI readiness signal."
        }
    }

    return hybrid_result