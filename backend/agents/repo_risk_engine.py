from typing import Dict
def clamp(value: float, min_value=0, max_value=100):
    return max(min_value, min(max_value, int(value)))
def compute_repo_risk_score(
    architecture_health: float,
    max_dependency_depth: int,
    cycle_count: int,
    avg_dependents: float,
    high_impact_file_count: int,
    impact_scores_average: float,
) -> Dict:
    # -------------------------
    # 1️⃣ Architecture Stability
    # -------------------------
    architecture_score = architecture_health
    depth_penalty = max_dependency_depth * 5
    cycle_penalty = cycle_count * 15
    architecture_score = architecture_score - depth_penalty - cycle_penalty
    architecture_score = clamp(architecture_score)
    # -------------------------
    # 2️⃣ Dependency Fragility
    # -------------------------
    dependency_risk = avg_dependents * 10
    dependency_risk += high_impact_file_count * 5
    dependency_risk = clamp(dependency_risk)
    # -------------------------
    # 3️⃣ Bus Factor Risk
    # -------------------------
    bus_factor_risk = high_impact_file_count * 8
    bus_factor_risk = clamp(bus_factor_risk)
    # -------------------------
    # 4️⃣ Change Volatility
    # -------------------------
    volatility_risk = impact_scores_average * 6
    volatility_risk = clamp(volatility_risk)
    # -------------------------
    # 5️⃣ Overall Score
    # -------------------------
    overall_score = (
        architecture_score * 0.4
        + (100 - dependency_risk) * 0.2
        + (100 - bus_factor_risk) * 0.2
        + (100 - volatility_risk) * 0.2
    )
    overall_score = clamp(overall_score)
    # -------------------------
    # Classification
    # -------------------------
    if overall_score >= 80:
        classification = "HEALTHY"
    elif overall_score >= 60:
        classification = "STABLE"
    elif overall_score >= 40:
        classification = "MODERATE RISK"
    elif overall_score >= 20:
        classification = "HIGH RISK"
    else:
        classification = "CRITICAL"
    return {
        "overall_score": overall_score,
        "classification": classification,
        "architecture_score": architecture_score,
        "dependency_risk": dependency_risk,
        "bus_factor_risk": bus_factor_risk,
        "volatility_risk": volatility_risk,
    }