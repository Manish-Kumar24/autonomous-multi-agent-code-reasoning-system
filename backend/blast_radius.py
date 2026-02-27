import networkx as nx
from collections import deque
def build_reverse_graph(G: nx.DiGraph):
    return G.reverse(copy=False)
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