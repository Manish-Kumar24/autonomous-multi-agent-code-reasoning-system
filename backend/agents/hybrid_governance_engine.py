from agents.policy_config import GovernancePolicy
def compute_hybrid_merge_decision(pr_data: dict) -> dict:
    risk_score = pr_data.get("pr_risk_score", 0)
    depth = pr_data.get("max_impact_depth", 0)
    ai_data = pr_data.get("ai_analysis", {})
    ai_signal = ai_data.get("merge_readiness", "MEDIUM")
    governance_score = 0
    risk_component = (risk_score / 100) * 50
    depth_component = min(30, depth * 3)  # reduce depth amplification
    governance_score += risk_component
    governance_score += depth_component
    if ai_signal == "LOW":
        governance_score += GovernancePolicy.AI_LOW_WEIGHT
    elif ai_signal == "MEDIUM":
        governance_score += GovernancePolicy.AI_MEDIUM_WEIGHT
    else:
        governance_score += GovernancePolicy.AI_HIGH_WEIGHT
    # Trivial safety guard
    if risk_score < 25 and depth < 8:
        final_decision = "REVIEW_REQUIRED"
        level = "MODERATE"
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