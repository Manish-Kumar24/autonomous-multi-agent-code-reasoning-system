from agents.policy_config import GovernancePolicy
def compute_hybrid_merge_decision(pr_data: dict) -> dict:
    risk_score = pr_data.get("pr_risk_score", 0)
    depth = pr_data.get("max_impact_depth", 0)
    ai_data = pr_data.get("ai_analysis", {})
    ai_signal = ai_data.get("merge_readiness", "MEDIUM")
    governance_score = 0
    governance_score += min(50, risk_score * GovernancePolicy.RISK_WEIGHT)
    governance_score += min(30, depth * GovernancePolicy.DEPTH_WEIGHT)
    if ai_signal == "LOW":
        governance_score += GovernancePolicy.AI_LOW_WEIGHT
    elif ai_signal == "MEDIUM":
        governance_score += GovernancePolicy.AI_MEDIUM_WEIGHT
    else:
        governance_score += GovernancePolicy.AI_HIGH_WEIGHT
    if governance_score >= GovernancePolicy.BLOCK_THRESHOLD:
        final_decision = "BLOCK"
        level = "CRITICAL"
    elif governance_score >= GovernancePolicy.REVIEW_THRESHOLD:
        final_decision = "REVIEW_REQUIRED"
        level = "MODERATE"
    else:
        final_decision = "ALLOW"
        level = "SAFE"
    return {
        "hybrid_governance": {
            "governance_score": round(governance_score, 2),
            "governance_level": level,
            "final_merge_decision": final_decision,
            "policy_used": {
                "risk_weight": GovernancePolicy.RISK_WEIGHT,
                "depth_weight": GovernancePolicy.DEPTH_WEIGHT,
                "block_threshold": GovernancePolicy.BLOCK_THRESHOLD
            }
        }
    }