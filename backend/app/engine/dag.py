"""DAG definition model and topological sort for workflow orchestration.

Provides ``WorkflowDag`` — a container that holds nodes and edges for a
workflow DAG — and ``topological_sort`` which returns a layered list of
nodes where each layer can be executed in parallel.
"""

from collections import defaultdict, deque


class WorkflowDag:
    """A directed acyclic graph (DAG) representing a workflow.

    Parameters
    ----------
    nodes : list[dict]
        Each dict must contain at least ``"id"``.
    edges : list[dict]
        Each dict must contain ``"source"`` and ``"target"`` keys.
    """

    def __init__(self, nodes: list[dict], edges: list[dict]):
        self.nodes = nodes
        self.edges = edges
        self._node_map = {n["id"]: n for n in nodes}
        self._build_adjacency()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_adjacency(self):
        """Build the adjacency list and in-degree map from edges."""
        self.in_degree: dict[str, int] = defaultdict(int)
        self.graph: dict[str, list[str]] = defaultdict(list)

        for node in self.nodes:
            self.in_degree[node["id"]]  # ensure every node has an entry

        for edge in self.edges:
            src = edge["source"]
            tgt = edge["target"]
            self.graph[src].append(tgt)
            self.in_degree[tgt] += 1

    # ------------------------------------------------------------------
    # Public query methods
    # ------------------------------------------------------------------

    def get_node(self, node_id: str) -> dict | None:
        """Return the node dict for *node_id*, or *None* if not found."""
        return self._node_map.get(node_id)

    def get_upstream_nodes(self, node_id: str) -> list[dict]:
        """Return all transitive upstream (predecessor) nodes of *node_id*.

        Performs a breadth-first traversal backwards through the edge list
        to collect every node that can reach *node_id*.
        """
        visited: set[str] = set()
        queue: deque[str] = deque([node_id])
        upstream: list[dict] = []

        while queue:
            current = queue.popleft()
            for edge in self.edges:
                if edge["target"] == current and edge["source"] not in visited:
                    visited.add(edge["source"])
                    source_node = self._node_map.get(edge["source"])
                    if source_node is not None:
                        upstream.append(source_node)
                    queue.append(edge["source"])
        return upstream


def topological_sort(dag: WorkflowDag) -> list[list[dict]]:
    """Layered topological sort of *dag*.

    Returns a list of **layers**. Each layer is a list of node dicts whose
    nodes have no dependencies on other nodes in the same layer and can
    therefore be executed in parallel. Layers are ordered sequentially.

    Raises
    ------
    ValueError
        If the DAG contains a cycle.
    """
    in_degree = dag.in_degree.copy()
    graph = dag.graph
    node_map = dag._node_map

    # Seed the queue with all nodes that have zero in-degree.
    queue: deque[str] = deque(
        nid for nid, deg in in_degree.items() if deg == 0
    )

    levels: list[list[dict]] = []

    while queue:
        layer_nodes: list[dict] = []
        for _ in range(len(queue)):
            nid = queue.popleft()
            layer_nodes.append(node_map[nid])
            for neighbor in graph[nid]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        levels.append(layer_nodes)

    # If any edges remain unprocessed the graph contains a cycle.
    if sum(in_degree.values()) > 0:
        raise ValueError("DAG contains a cycle")

    return levels
