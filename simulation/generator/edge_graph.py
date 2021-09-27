from dataclasses import dataclass

@dataclass
class EdgeNode:
    """Encapsulates a node in a graph of edge nodes."""
    identifier: str
    neighbours: list[str]


@dataclass
class EdgeGraph:
    """Represents a graph of connected EdgeNode objects."""
    graph: dict[str, EdgeNode]

    def get_node(self, by_identifier: str):
        return self.graph.get(by_identifier, None)
