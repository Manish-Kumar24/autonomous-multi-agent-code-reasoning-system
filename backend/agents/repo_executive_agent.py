import os, json, re
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_repo_executive_summary(metrics, score_data):
    prompt = f"""
        You are a CTO-level engineering advisor.
        Given these repository metrics:
        Architecture Score: {score_data['architecture_score']}
        Dependency Risk: {score_data['dependency_risk']}
        Bus Factor Risk: {score_data['bus_factor_risk']}
        Volatility Risk: {score_data['volatility_risk']}
        Overall Score: {score_data['overall_score']}
        Classification: {score_data['classification']}
        Max Dependency Depth: {metrics['max_dependency_depth']}
        Cycle Count: {metrics['cycle_count']}
        Average Dependents: {metrics['avg_dependents']}
        High Impact Files: {metrics['high_impact_file_count']}
        Impact Score Average: {metrics['impact_scores_average']}
        Provide structured JSON with:
        - executive_summary
        - primary_architectural_weakness
        - immediate_engineering_action
        - long_term_structural_recommendation
        """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}],
    )
    raw_output = response.choices[0].message.content
    # 🔥 Remove markdown fences if present
    cleaned = re.sub(r"```json|```", "", raw_output).strip()
    try:
        return json.loads(cleaned)
    except:
        return {
            "executive_summary": "Unable to parse executive analysis.",
            "raw_output": raw_output
        }