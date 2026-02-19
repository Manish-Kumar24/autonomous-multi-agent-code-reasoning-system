import os, re, networkx as nx

IGNORED_DIRS = {
    "node_modules",
    ".git",
    "dist",
    "build",
    "venv",
    "__pycache__",
    "test",
    "tests",
    "__tests__",
    "examples",
    "docs",
    "coverage",
    "fixtures",
    "scripts",
    "benchmark",
    "__mocks__"
}

IMPORT_REGEX = [
    r"import\s+.*\s+from\s+['\"](.*?)['\"]",
    r"require\(['\"](.*?)['\"]\)",
    r"from\s+([\w\.]+)\s+import",
    r"import\s+([\w\.]+)"
]

ENTRY_HINTS = (
    "index",
    "main",
    "app",
    "server",
    "root",
    "bootstrap"
)

def is_internal_import(path: str) -> bool:
    return path.startswith(".")

def extract_imports(file_path):
    imports = []
    try:
        with open(file_path, "r", errors="ignore") as f:
            content = f.read()
        for pattern in IMPORT_REGEX:
            matches = re.findall(pattern, content)
            for m in matches:
                if is_internal_import(m):
                    imports.append(m)
    except Exception as e:
        print(f"[IMPORT PARSE ERROR] {file_path} -> {e}")
    return imports

GRAPH_CACHE = {}

def build_dependency_graph(repo_path):
    if repo_path in GRAPH_CACHE:
        return GRAPH_CACHE[repo_path]
    G = nx.DiGraph()
    repo_files = set()
    # PASS 1 — collect files
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for file in files:
            if file.endswith((".js", ".ts", ".py")):
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, repo_path)
                repo_files.add(relative_path)
                G.add_node(relative_path)
    print("TOTAL FILES:", len(repo_files))
    # PASS 2 — build edges
    for file in repo_files:
        full_path = os.path.join(repo_path, file)
        imports = extract_imports(full_path)
        for imp in imports:
            base_dir = os.path.dirname(file)
            resolved_path = os.path.normpath(
                os.path.join(base_dir, imp)
            )
            candidates = [
                resolved_path,
                resolved_path + ".js",
                resolved_path + ".ts",
                resolved_path + ".py",
                os.path.join(resolved_path, "index.js"),
            ]
            for candidate in candidates:
                if candidate in repo_files:
                    G.add_edge(file, candidate)
    print("TOTAL EDGES:", len(G.edges))
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
        hint_bonus = any(h in node.lower() for h in ENTRY_HINTS)
        depth_penalty = node.count(os.sep)
        root_bonus = 3 if os.sep not in node else 0
        return (degree * 2) + hint_bonus - depth_penalty + root_bonus

    # ⭐ Health Score Calculator (NEW — Senior Signal)
    def compute_health_score(G, cycles_detected, max_depth, bus_factor_risks):
        score = 10.0
        # Cycles are serious architectural smell
        if cycles_detected:
            score -= 3.5
        # Deep dependency chains increase fragility
        if max_depth is not None:
            if max_depth >= 6:
                score -= 2.5
            elif max_depth >= 4:
                score -= 1.2
        # Bus factor concentration
        if bus_factor_risks:
            top_dependents = bus_factor_risks[0]["dependents"]
            if top_dependents >= 10:
                score -= 2
            elif top_dependents >= 5:
                score -= 1
        return round(max(score, 1.0), 1)
    # ⭐ Convert Score → Label
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
    # ⭐ Bus Factor Risks (high in-degree)
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
    # ⭐ Leaf nodes
    terminal_modules = sorted(
        [node for node in G.nodes if G.out_degree(node) == 0],
        key=lambda x: G.in_degree(x),
        reverse=True
    )[:5]
    # ⭐ Safe cycle detection
    cycles_detected = not nx.is_directed_acyclic_graph(G)
    # ⭐ Dependency Depth
    if not cycles_detected and len(G.nodes) > 0:
        max_dependency_depth = nx.dag_longest_path_length(G)
    else:
        max_dependency_depth = None
    # ⭐ Architecture Health Score (NEW)
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