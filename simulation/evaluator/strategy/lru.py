from simulation.evaluator.cache.cache_item import CacheItem
from simulation.evaluator.cache.lru_cache_linked import LRUCache
from simulation.evaluator.strategy.strategy import CacheStrategy

class LRUStrategy(CacheStrategy):
    def __init__(self, nodes: dict[str, dict[str, any]]):
        super().__init__({ name: self.build_node(settings)
                       for name, settings in nodes.items() })

    def build_node(self, from_settings: dict[str, any]) -> LRUCache:
        return LRUCache(capacity=int(from_settings["capacity"]))

    def handle_request(self, for_user: str, for_node: str, content: CacheItem, at_timestamp: int):
        node = self.nodes[for_node]
        if node.retrieve(content.identifier, at_timestamp) != None:
            node.cache_metrics.track_hit(content.size())
        else:
            node.cache_metrics.track_miss()
            node.cache_metrics.track_request_origin()
            node.store(content.identifier, content, at_timestamp)
            node.cache_metrics.track_bytes_origin(content.size())
