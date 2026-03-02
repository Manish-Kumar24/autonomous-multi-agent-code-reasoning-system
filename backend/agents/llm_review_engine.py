import json
import re
from core.llm import ask_llama
from utils.logger import get_logger

logger = get_logger("llm-review-engine")

REQUIRED_KEYS = [
    "review_focus",
    "testing_strategy",
    "merge_readiness",
    "risk_explanation",
    "recommended_actions"
]

RISK_CONTEXT = {
    "LOW": "Minor change. Avoid overreaction. Keep guidance proportional.",
    "MODERATE": "Moderate impact. Validate integration points carefully.",
    "HIGH": "High dependency impact. Focus on regression risk and edge cases.",
    "CRITICAL": "System-level risk. Require rollback plan and production validation."
}

def fallback_review_template():
    return {
        "review_focus": "AI analysis unavailable. Review impacted modules manually.",
        "testing_strategy": "Execute unit and integration tests aligned with risk classification.",
        "merge_readiness": "MEDIUM",
        "risk_explanation": "AI response failed validation. Deterministic governance applied.",
        "recommended_actions": [
            "Manual senior engineer review required"
        ]
    }

def safe_parse_llm_response(response: str) -> dict:
    try:
        cleaned = re.sub(r"```.*?\n", "", response)
        cleaned = re.sub(r"```", "", cleaned).strip()
        parsed = json.loads(cleaned)
        if not all(k in parsed for k in REQUIRED_KEYS):
            raise ValueError("Missing required keys")
        if parsed["merge_readiness"] not in ["LOW", "MEDIUM", "HIGH"]:
            raise ValueError("Invalid merge readiness value")
        if not isinstance(parsed["recommended_actions"], list):
            raise ValueError("recommended_actions must be list")
        return parsed
    except Exception as e:
        logger.warning(f"LLM JSON validation failed: {e}")
        return fallback_review_template()

def generate_llm_review(pr_data: dict) -> dict:
    classification = pr_data.get("classification", "LOW")
    risk_score = pr_data.get("pr_risk_score", 0)
    total_files = pr_data.get("total_files_affected", 0)
    max_depth = pr_data.get("max_impact_depth", 0)
    modules = pr_data.get("high_risk_modules", [])
    diff_metrics = pr_data.get("diff_risk", {})
    semantic = pr_data.get("semantic_risk", {})
    confidence_score = pr_data.get("confidence_score", 0.5)
    risk_context_text = RISK_CONTEXT.get(classification, "")

    system_prompt = """
You are a senior backend governance reviewer.

You do NOT compute risk.
You interpret deterministic risk signals.

Respond ONLY in valid JSON.
Do not add commentary outside JSON.
Be concise, structured, and actionable.
"""

    user_prompt = f"""
PR RISK SUMMARY:
Risk Score: {risk_score}
Classification: {classification}
Total Files Affected: {total_files}
Max Dependency Depth: {max_depth}
High Risk Modules: {modules}
Diff Intensity: {diff_metrics.get("change_intensity", 0)}
Critical Modification Score: {diff_metrics.get("critical_modification_score", 0)}
Semantic Risk Score: {semantic.get("semantic_score", 0)}

Risk Context Instruction:
{risk_context_text}

TASK:
1. Identify where reviewers must focus.
2. Suggest testing strategy aligned to risk.
3. Assess merge readiness (LOW/MEDIUM/HIGH).
4. Explain why the risk is at this level (3–4 sentences).
5. Recommend safeguards before merging.

Return strict JSON:
{{
  "review_focus": str,
  "testing_strategy": str,
  "merge_readiness": "LOW|MEDIUM|HIGH",
  "risk_explanation": str,
  "recommended_actions": list[str]
}}
"""

    try:
        response = ask_llama(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )

        parsed = safe_parse_llm_response(response)

        if confidence_score < 0.6:
            parsed["recommended_actions"].append(
                "⚠ AI confidence low. Mandatory human validation required."
            )

        return parsed

    except Exception as e:
        logger.exception("LLM request failed")
        return fallback_review_template()