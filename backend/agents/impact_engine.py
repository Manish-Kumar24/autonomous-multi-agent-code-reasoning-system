import os, re, json, ast, networkx as nx
from typing import List
from blast_radius import (
    build_reverse_graph,
    compute_blast_radius
)
IGNORED_DIRS = {
    "node_modules", ".git", "dist", "build", "venv",
    "__pycache__", "test", "tests", "__tests__", "examples",
    "docs", "docs_src", "tutorial", "tutorials",
    "coverage", "fixtures", "scripts",
    "benchmark", "__mocks__"
}
GRAPH_CACHE = {}

def extract_imports(file_path):
    imports = []
    if not file_path.endswith(".py"):
        return imports
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except SyntaxError:
            # Fallback regex-based extraction
            for line in source.splitlines():
                line = line.strip()
                if line.startswith("import "):
                    module = line.replace("import ", "").split(" as ")[0]
                    imports.append(module)
                elif line.startswith("from "):
                    module = line.replace("from ", "").split(" import ")[0]
                    imports.append(module)
    except Exception as e:
        print(f"[IMPORT PARSE ERROR] {file_path} -> {e}")
    return imports

def build_dependency_graph(repo_path):
    repo_path = os.path.abspath(repo_path)
    if repo_path in GRAPH_CACHE:
        return GRAPH_CACHE[repo_path]
    print("SCANNING PATH:", repo_path)
    G = nx.DiGraph()
    repo_files = set()
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [
            d for d in dirs
            if d not in IGNORED_DIRS
            and not d.startswith("docs")
            and not d.startswith("example")
        ]
        for file in files:
            if file.endswith((".py")):
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, repo_path).replace("\\", "/").lstrip("./")
                repo_files.add(relative_path)
                G.add_node(relative_path)
    print("TOTAL FILES:", len(repo_files))
    for file in repo_files:
        full_path = os.path.join(repo_path, file)
        imports = extract_imports(full_path)
        for imp in imports:
            module_path = imp.replace(".", "/")
            # try matching anywhere inside repo (more robust)
            for repo_file in repo_files:
                if repo_file.endswith(module_path + ".py") or \
                repo_file.endswith(module_path + "/__init__.py"):
                    G.add_edge(file, repo_file)
    print("TOTAL EDGES:", len(G.edges))
    print("GRAPH SAMPLE EDGES:", list(G.edges())[:20])
    GRAPH_CACHE[repo_path] = G
    return G
def analyze_graph(G):
    if len(G.nodes) == 0:
        return {
            "probable_entry_points": [],
            "bus_factor_risks": [],
            "terminal_modules": [],
            "cycles_detected": False
        }
    def entry_score(node_tuple):
        node, degree = node_tuple
        hint_bonus = 0
        depth_penalty = node.count(os.sep)
        root_bonus = 3 if os.sep not in node else 0
        return (degree * 2) + hint_bonus - depth_penalty + root_bonus
    def compute_health_score(G, cycles_detected, max_depth, bus_factor_risks):
        score = 10.0
        if cycles_detected:
            score -= 3.5
        if max_depth is not None:
            if max_depth >= 6:
                score -= 2.5
            elif max_depth >= 4:
                score -= 1.2
        if bus_factor_risks:
            top_dependents = bus_factor_risks[0]["dependents"]
            if top_dependents >= 10:
                score -= 2
            elif top_dependents >= 5:
                score -= 1
        return round(max(score, 1.0), 1)
    def health_label(score):
        if score >= 8.5:
            return "EXCELLENT"
        elif score >= 7:
            return "GOOD"
        elif score >= 5:
            return "MODERATE"
        else:
            return "HIGH_RISK"
    probable_entry_points = sorted(
        G.out_degree,
        key=entry_score,
        reverse=True
    )[:5]
    probable_entry_points = [node for node, _ in probable_entry_points]
    bus_factor_risks = sorted(
        [(node, deg) for node, deg in G.in_degree if deg > 0],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    bus_factor_risks = [
        {
            "file": node,
            "dependents": degree
        }
        for node, degree in bus_factor_risks
    ]
    terminal_modules = sorted(
        [node for node in G.nodes if G.out_degree(node) == 0],
        key=lambda x: G.in_degree(x),
        reverse=True
    )[:5]
    cycles_detected = not nx.is_directed_acyclic_graph(G)
    if not cycles_detected and len(G.nodes) > 0:
        max_dependency_depth = nx.dag_longest_path_length(G)
    else:
        max_dependency_depth = None
    architecture_health_score = compute_health_score(
        G,
        cycles_detected,
        max_dependency_depth,
        bus_factor_risks
    )
    architecture_health = health_label(architecture_health_score)
    return {
        "probable_entry_points": probable_entry_points,
        "bus_factor_risks": bus_factor_risks,
        "terminal_modules": terminal_modules,
        "cycles_detected": cycles_detected,
        "max_dependency_depth": max_dependency_depth,
        "architecture_health_score": architecture_health_score,
        "architecture_health": architecture_health,
        "graph_stats": {
            "files": len(G.nodes),
            "edges": len(G.edges),
            "density": round(nx.density(G), 4)
        }
    }
def dependency_agent(repo_path):
    graph = build_dependency_graph(repo_path)
    intelligence = analyze_graph(graph)
    return intelligence
def compute_risk_score(direct, transitive, depth):
    return (direct * 2) + (transitive * 1.5) + depth
def classify_risk(score):
    if score >= 20:
        return "CRITICAL"
    elif score >= 13:
        return "HIGH"
    elif score >= 6:
        return "MODERATE"
    else:
        return "LOW"
def analyze_impact(repo_path: str, changed_files: List[str]):
    print("IMPACT ANALYZER REPO PATH:", repo_path)
    print("EXISTS?", os.path.exists(repo_path))
    G = build_dependency_graph(repo_path)
    reverse_graph = build_reverse_graph(G)
    normalized_changed_files = []
    for f in changed_files:
        f = f.replace("\\", "/")
        f = f.lstrip("./")
        normalized_changed_files.append(f)
    valid_files = []
    graph_nodes = {node.replace("\\", "/").lstrip("./") for node in G.nodes}
    for changed in normalized_changed_files:
        for node in graph_nodes:
            if node.endswith(changed):
                valid_files.append(node)
    print("VALID FILES:", valid_files)
    print("TOTAL GRAPH NODES:", len(G.nodes))
    print("SAMPLE NODES:", list(G.nodes)[:20])
    print("CHANGED FILES:", normalized_changed_files)
    if not valid_files:
        return [{
            "file": "INVALID_INPUT",
            "risk_score": 0,
            "risk_level": "LOW",
            "direct_dependents": 0,
            "transitive_dependents": 0,
            "depth": 0,
            "error": "Changed files do not belong to analyzed repository",
            "debug_changed_files": changed_files,
            "debug_available_files": list(G.nodes)[:10]
        }]
    results = []
    for file in valid_files:
        if file not in G:
            continue
        dependents, depth = compute_blast_radius(file, reverse_graph)
        direct = len(list(reverse_graph.successors(file)))
        transitive = len(dependents)
        score = compute_risk_score(direct, transitive, depth)
        risk = classify_risk(score)
        results.append({
            "file": file,
            "risk_score": round(score, 2),
            "risk_level": risk,
            "direct_dependents": direct,
            "transitive_dependents": transitive,
            "depth": depth
        })
    return results