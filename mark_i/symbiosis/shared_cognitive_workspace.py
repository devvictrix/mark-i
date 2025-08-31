import logging
from typing import Any, Dict

# In a real implementation, you'd use a library like networkx.
# For this simulation, we'll use a simple dict-based graph.
# import networkx as nx

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.symbiosis.workspace")


class SharedCognitiveWorkspace:
    """
    Manages the shared mental model between the user and the AI,
    represented as a graph.
    """

    def __init__(self):
        # self.graph = nx.MultiDiGraph()
        self.graph = {}  # Simplified graph: {node_id: {"data": ..., "edges": {related_id: "relation_type"}}}
        self.node_counter = 0
        logger.info("SharedCognitiveWorkspace initialized.")

    def add_node(self, data: Any, relationships: Dict[int, str] | None = None) -> int:
        """Adds a new concept or piece of data to the workspace."""
        node_id = self.node_counter
        self.graph[node_id] = {"data": data, "edges": {}}
        if relationships:
            for target_id, relation in relationships.items():
                if target_id in self.graph:
                    self.graph[node_id]["edges"][target_id] = relation
        self.node_counter += 1
        logger.info(f"Added node {node_id} to workspace. Data: '{str(data)[:50]}'")
        return node_id

    def get_full_workspace_as_text(self) -> str:
        """Returns a string representation of the graph for AI reasoning."""
        return str(self.graph)
