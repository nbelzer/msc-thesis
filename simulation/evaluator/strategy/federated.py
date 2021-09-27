from simulation.evaluator.cache.cache_item import CacheItem
from simulation.evaluator.cache.lru_cache import LRUCache
from simulation.evaluator.strategy.strategy import CacheStrategy

class FederatedStrategy(CacheStrategy):
    def __init__(self, nodes: dict[str, dict[str, any]]):
        super().__init__({ name: self.build_node(settings)
                           for name, settings in nodes.items() })

    def build_node(self, from_settings: dict[str, any]) -> LRUCache:
        return LRUCache(capacity=int(from_settings["capacity"]))

    def handle_request(self, for_user: str, for_node: str, content: CacheItem, at_timestamp: int):
        node = self.nodes[for_node]
        target_node_id = self.__node_for_identifier(content.identifier)
        target_node = self.nodes[target_node_id]

        if target_node.retrieve(content.identifier, at_timestamp) != None:
            target_node.cache_metrics.track_hit(content.size())
        else:
            target_node.cache_metrics.track_miss()
            target_node.cache_metrics.track_request_origin()
            target_node.store(content.identifier, content, at_timestamp)
            target_node.cache_metrics.track_bytes_origin(content.size())

        if target_node_id != for_node:
            node.cache_metrics.track_request_neighbour()
            node.cache_metrics.track_request_neighbour_success(content.size())


    def __node_for_identifier(self, identifier: str):
        """Hashes the identifier and selects the appropriate node based
        on that hash.
        """
        h = identifier.__hash__()
        return list(self.nodes.keys())[h % len(self.nodes)]
