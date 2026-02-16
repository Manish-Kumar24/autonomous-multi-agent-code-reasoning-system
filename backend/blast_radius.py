import networkx as nx
from collections import deque

# ✅ Reverse Graph (1 line with NetworkX — very senior)
def build_reverse_graph(G: nx.DiGraph):
    return G.reverse(copy=False)

from collections import deque

def compute_blast_radius(target_file, reverse_graph):

    visited = set()
    queue = deque([(target_file, 0)])

    max_depth = 0

    while queue:
        current, depth = queue.popleft()

        for dependent in reverse_graph.successors(current):

            if dependent not in visited:
                visited.add(dependent)

                next_depth = depth + 1
                max_depth = max(max_depth, next_depth)

                queue.append((dependent, next_depth))

    return visited, max_depth

# ✅ Criticality heuristic
def calculate_criticality(dependent_count, max_depth):

    score = (dependent_count * 1.5) + (max_depth * 2)

    if score > 20:
        risk = "HIGH"
    elif score > 10:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return round(score, 2), risk

# ✅ Executive-friendly severity layer
def calculate_severity(score, depth):
    
    if score >= 25 or depth >= 5:
        return "CRITICAL"
    
    elif score >= 15:
        return "HIGH"
    
    elif score >= 8:
        return "MODERATE"
    
    else:
        return "LOW"


def generate_reason(file, direct, transitive, depth, risk):
    
    if risk == "HIGH":
        return (
            "Critical core module with widespread dependency reach. "
            "Failure could cascade across multiple execution paths and severely impact system stability."
        )

    elif risk == "MEDIUM":
        return (
        f"This module is depended on by {transitive} files with an impact depth of {depth}. "
        "Changes here may propagate through the system and require careful regression testing."
        )


    else:
        return (
            "Localized module with limited dependency exposure. "
            "Failure is unlikely to propagate widely."
        )
