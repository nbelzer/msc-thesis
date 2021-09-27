from .cooperative_lru import CooperativeLRUStrategy

class NeighbouringLRUStrategy(CooperativeLRUStrategy):
    node_map: dict[str, list[str]]

    def __init__(self, nodes: dict[str, dict[str, any]], node_map: dict[str, list[str]], outsource_resources: bool = False):
        super().__init__(nodes, 0, outsource_resources)
        self.node_map = node_map

    def find_latest_nodes(self, user, node, content_neighbour) -> list[str]:
        return [ x for x in self.node_map[node] if x != node and x != content_neighbour ]
