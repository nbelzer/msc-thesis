from dataclasses import replace
from simulation.evaluator.cache.cache import Cache
from collections import defaultdict

class CacheStrategy:
    user_node_map: dict[str, list[str]]
    nodes: dict[str, Cache]

    def __init__(self, nodes: dict[str, Cache]):
        self.user_node_map = defaultdict(list)
        self.nodes = nodes

    def handle_iteration(self, iteration: int):
        pass

    def handle_request(self, for_node: str):
        raise NotImplementedError

    def handle_node_connect(self, for_user: str, for_node: str):
        self.user_node_map[for_user].append(for_node)

    def handle_node_disconnect(self, for_user: str):
        pass

    def capture_statistics(self):
        return { key: replace(node.cache_metrics) for key, node in self.nodes.items() }
