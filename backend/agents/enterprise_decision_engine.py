def build_enterprise_decision(pr_data: dict) -> dict:
    score = pr_data.get("pr_risk_score", 0)
    classification = pr_data.get("classification", "LOW")
    depth = pr_data.get("max_impact_depth", 0)
    # ---------------------------
    # Reviewer Suggestion Logic
    # ---------------------------
    if classification == "HIGH":
        primary = "Senior Maintainer"
        secondary = "Module Owner"
        approvals = 2
        architecture_review = True
        security_review = True
    elif classification == "MEDIUM":
        primary = "Module Owner"
        secondary = "Peer Reviewer"
        approvals = 1
        architecture_review = False
        security_review = False
    else:
        primary = "Peer Reviewer"
        secondary = None
        approvals = 1
        architecture_review = False
        security_review = False
    reviewer_suggestion = {
        "primary_reviewer": primary,
        "secondary_reviewer": secondary,
        "approvals_required": approvals,
        "architecture_review": architecture_review,
        "security_review": security_review,
        "reason": f"{classification} downstream impact detected"
    }
    # ---------------------------
    # Testing Recommendation
    # ---------------------------
    testing_recommendation = {
        "unit_testing": "Mandatory",
        "integration_testing": "Required" if classification != "LOW" else "Optional",
        "regression_testing": "Required" if classification == "HIGH" else "Recommended",
        "performance_testing": "Recommended" if depth >= 3 else "Optional",
        "security_testing": "Required" if classification == "HIGH" else "Optional",
        "test_coverage_target": ">= 80%" if classification == "HIGH" else ">= 70%"
    }
    # ---------------------------
    # Merge Control
    # ---------------------------
    if classification == "HIGH":
        merge_decision = "BLOCK"
        decision_reason = "High risk with significant architectural impact."
    elif classification == "MEDIUM":
        merge_decision = "REVIEW_REQUIRED"
        decision_reason = "Moderate risk. Review required before merge."
    else:
        merge_decision = "ALLOW"
        decision_reason = "Low risk. Safe to merge."

    merge_control = {
        "merge_decision": merge_decision,
        "decision_reason": decision_reason
    }
    # ---------------------------
    # Confidence Engine
    # ---------------------------
    confidence_score = min(100.0, 60 + depth * 10)
    if confidence_score > 85:
        confidence_level = "VERY HIGH"
    elif confidence_score > 70:
        confidence_level = "HIGH"
    else:
        confidence_level = "MEDIUM"
    confidence = {
        "confidence_score": confidence_score,
        "confidence_level": confidence_level
    }
    return {
        "reviewer_suggestion": reviewer_suggestion,
        "testing_recommendation": testing_recommendation,
        "merge_control": merge_control,
        "confidence": confidence
    }