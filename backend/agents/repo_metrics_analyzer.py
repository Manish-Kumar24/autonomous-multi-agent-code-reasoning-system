import networkx as nx
def analyze_repository(graph):
    total_nodes = graph.number_of_nodes()
    total_edges = graph.number_of_edges()
    if total_nodes == 0:
        return {
            "architecture_health": 100,
            "max_dependency_depth": 0,
            "cycle_count": 0,
            "avg_dependents": 0,
            "high_impact_file_count": 0,
            "impact_scores_average": 0,
        }
    # ----------------------------------
    # 1️⃣ Max Dependency Depth
    # ----------------------------------
    max_dependency_depth = 0
    for node in graph.nodes():
        try:
            lengths = nx.single_source_shortest_path_length(graph, node)
            if lengths:
                depth = max(lengths.values())
                max_dependency_depth = max(max_dependency_depth, depth)
        except:
            continue
    # ----------------------------------
    # 2️⃣ Cycle Count
    # ----------------------------------
    try:
        cycles = list(nx.simple_cycles(graph))
        cycle_count = len(cycles)
    except:
        cycle_count = 0
    # ----------------------------------
    # 3️⃣ Average Dependents
    # ----------------------------------
    dependents_counts = [graph.out_degree(n) for n in graph.nodes()]
    avg_dependents = sum(dependents_counts) / total_nodes
    # ----------------------------------
    # 4️⃣ High Impact Files
    # Definition: files with above-average dependents
    # ----------------------------------
    high_impact_files = [
        n for n in graph.nodes()
        if graph.out_degree(n) > avg_dependents
    ]
    high_impact_file_count = len(high_impact_files)
    # ----------------------------------
    # 5️⃣ Impact Score Average
    # Simple blast approximation:
    # number of reachable nodes from each node
    # ----------------------------------
    impact_scores = []
    for node in graph.nodes():
        try:
            reachable = nx.descendants(graph, node)
            impact_scores.append(len(reachable))
        except:
            impact_scores.append(0)

    impact_scores_average = sum(impact_scores) / total_nodes
    # ----------------------------------
    # 6️⃣ Architecture Health
    # Base score starts at 100 and penalizes complexity
    # ----------------------------------
    architecture_health = 100
    architecture_health -= max_dependency_depth * 5
    architecture_health -= cycle_count * 10
    architecture_health = max(0, min(100, architecture_health))
    return {
        "architecture_health": architecture_health,
        "max_dependency_depth": max_dependency_depth,
        "cycle_count": cycle_count,
        "avg_dependents": avg_dependents,
        "high_impact_file_count": high_impact_file_count,
        "impact_scores_average": impact_scores_average,
    }