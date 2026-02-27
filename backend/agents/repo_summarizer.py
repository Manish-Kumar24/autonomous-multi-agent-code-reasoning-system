import os, json
from core.llm import ask_llama
IMPORTANT_FILES = [
    "README.md",
    ".github/workflows",
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "tsconfig.json",
    "Dockerfile",
    "docker-compose.yml",
    ".env.example",
    "Makefile"
]
def read_important_files(repo_path: str) -> str:
    context_parts = []
    for file in IMPORTANT_FILES:
        path = os.path.join(repo_path, file)
        if os.path.exists(path):
            try:
                with open(path, "r", errors="ignore") as f:
                    if file.lower() in [
                        "dockerfile",
                        "docker-compose.yml",
                        "tsconfig.json",
                        ".env.example",
                        "makefile"
                    ]:
                        lines = f.readlines()
                        if len(lines) > 400:
                            content = "".join(lines[:300] + lines[-100:])
                        else:
                            content = "".join(lines)
                    else:
                        content = f.read(4000)
                    context_parts.append(
                        f"\n==== {file} ====\n{content}"
                    )
            except Exception:
                pass
    return "\n".join(context_parts)

def summarize_repo(repo_path: str):
    context = read_important_files(repo_path)
    if not context:
        return {
            "analysis": None,
            "explanation": "No important files found.",
            "error": True
        }
    messages = [
        {
            "role": "system",
            "content":
            """
You are a Principal Software Architect performing a deep technical audit of a code repository.
Your job is NOT to summarize casually.
Your job is to THINK like a senior engineer reviewing a production system.
Be analytical.
Be critical.
Avoid politeness.
Avoid vague statements.
If information is missing, infer intelligently from available signals such as dependencies, tooling, repo structure, and documentation.
------------------------------------------------
Return ONLY valid JSON first.
DO NOT wrap it in markdown.
DO NOT add numbering.
DO NOT explain before the JSON.
Use this schema:
{
  "system": "Name and type of the system",
  "tech_stack": ["languages", "frameworks", "major tools"],
  "architecture": "Monolith | Modular Monolith | Microservices | Serverless | Library | Framework | Monorepo | Unknown",
  "complexity": "Low | Medium | High | Very High",
  "production_ready": true,
  "risks": ["architectural or operational risks"],
  "notable_signals": ["important engineering indicators discovered in the repo"]
}
------------------------------------------------
ANALYSIS RULES:
• Complexity MUST be justified internally using signals like:
  - dependency count
  - build tooling
  - repo size
  - modular structure
  - testing surface
  - CI/CD presence
• NEVER leave "risks" empty.
Every real-world system has tradeoffs.
Common risks to consider:
- dependency explosion
- security attack surface
- scaling bottlenecks
- operational complexity
- insufficient testing
- upgrade fragility
- tight coupling
- developer experience friction
• "notable_signals" should highlight strong engineering practices such as:
- presence of tests
- linting
- monorepo tooling
- typed codebases
- CI pipelines
- code generation
- plugin systems
------------------------------------------------
After the JSON, write EXACTLY:
===EXPLANATION===
Then produce a sharp executive-level explanation (5–8 sentences).
Write like you are briefing a CTO.
Be dense.
Be technical.
No fluff.
No repetition.
No marketing language.
------------------------------------------------
"""
        },
        {
            "role": "user",
            "content": context
        }
    ]
    response = ask_llama(messages)
    try:
        json_part, explanation = response.split("===EXPLANATION===")
        parsed_json = json.loads(json_part.strip())
        return {
            "analysis": parsed_json,
            "explanation": explanation.strip(),
            "error": False
        }
    except Exception:
        return {
            "analysis": None,
            "explanation": response,
            "error": True
        }
def file_explainer_agent(code_content):
    messages = [
        {
            "role": "system",
            "content": """
You are a Staff Software Engineer performing a code review.
Explain the file with:
1. Purpose of the file
2. Core logic
3. Dependencies
4. Design patterns used
5. Potential bugs or risks
6. Skill level required to write this
7. One-line TLDR for executives
8. Improvement suggestions
9. Where this file sits in the overall architecture 
   (entrypoint, router, controller, config, core engine, etc.)
Avoid generic architecture criticism.
Only mention scalability concerns if there is real evidence:
- tightly coupled modules
- no service boundaries
- large shared state
- synchronous chains
Be precise. No fluff.
"""
        },
        {
            "role": "user",
            "content": code_content
        }
    ]
    return ask_llama(messages, temperature=0.1)