import os
import json

def detect_stack(repo_path: str):
    stack = {
        "backend": None,
        "frontend": None,
        "database": None,
        "testing": None,
        "language": None
    }
    # ---------- Detect Node.js from package.json ----------
    package_json = os.path.join(repo_path, "package.json")
    if os.path.exists(package_json):
        try:
            with open(package_json) as f:
                data = json.load(f)
            # Merge dependencies + devDependencies
            deps = data.get("dependencies", {})
            dev_deps = data.get("devDependencies", {})
            all_deps = {**deps, **dev_deps}
            dep_keys = [k.lower() for k in all_deps.keys()]
            # Set language if JS/TS detected
            if dep_keys:
                stack["language"] = "JavaScript/TypeScript"
            # Backend frameworks
            if "express" in dep_keys:
                stack["backend"] = "Node + Express"
            if "fastify" in dep_keys:
                stack["backend"] = "Fastify"
            # Frontend
            if "react" in dep_keys:
                stack["frontend"] = "React"
            if "next" in dep_keys:
                stack["frontend"] = "Next.js"
            if "vue" in dep_keys:
                stack["frontend"] = "Vue.js"
            # Database libs
            if "mongoose" in dep_keys or "mongodb" in dep_keys:
                stack["database"] = "MongoDB"
            if "pg" in dep_keys or "postgres" in dep_keys:
                stack["database"] = "PostgreSQL"
            if "mysql" in dep_keys:
                stack["database"] = "MySQL"
            # Testing
            if "jest" in dep_keys:
                stack["testing"] = "Jest"
            if "mocha" in dep_keys:
                stack["testing"] = "Mocha"
            if "chai" in dep_keys:
                stack["testing"] = "Chai"
        except Exception:
            pass
    # ---------- Detect Python from requirements.txt / pyproject.toml ----------
    requirements = os.path.join(repo_path, "requirements.txt")
    pyproject = os.path.join(repo_path, "pyproject.toml")
    # Python detection
    if os.path.exists(requirements) or os.path.exists(pyproject):
        stack["language"] = "Python"
    if os.path.exists(requirements):
        with open(requirements) as f:
            content = f.read().lower()
        if "fastapi" in content:
            stack["backend"] = "FastAPI"
        if "django" in content:
            stack["backend"] = "Django"
        if "pytest" in content:
            stack["testing"] = "PyTest"
        if "psycopg2" in content:
            stack["database"] = "PostgreSQL"
    if os.path.exists(pyproject):
        with open(pyproject) as f:
            content = f.read().lower()
        if "fastapi" in content:
            stack["backend"] = "FastAPI"
        if "django" in content:
            stack["backend"] = "Django"
        if "pytest" in content:
            stack["testing"] = "PyTest"
    # ---------- Fallback: Detect by file extensions ----------
    for subdir, _, files in os.walk(repo_path):
        for file in files:
            # Python
            if file.endswith(".py") and not stack["language"]:
                stack["language"] = "Python"
            # JS/TS
            if file.endswith((".js", ".jsx", ".ts", ".tsx")) and not stack["language"]:
                stack["language"] = "JavaScript/TypeScript"
    return stack
