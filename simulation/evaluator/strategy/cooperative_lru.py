from simulation.evaluator.cache.cache_item import CacheItem
from simulation.evaluator.cache.clru_cache import CooperativeLRUCache
from simulation.evaluator.strategy.strategy import CacheStrategy

class CooperativeLRUStrategy(CacheStrategy):
    node_trail_length: int
    outsource_resources: bool

    def __init__(self, nodes: dict[str, dict[str, any]], node_trail_length: int, outsource_resources: bool = False):
        super().__init__({ name: self.build_node(settings)
                           for name, settings in nodes.items() })
        self.node_trail_length = node_trail_length
        self.outsource_resources = outsource_resources

    def build_node(self, from_settings: dict[str, any]) -> CooperativeLRUCache:
        return CooperativeLRUCache(capacity=int(from_settings["capacity"]))

    def handle_request(self, for_user: str, for_node: str, content: CacheItem, at_timestamp: int):
        node = self.nodes[for_node]
        if node.retrieve(content.identifier, at_timestamp) != None:
            node.cache_metrics.track_hit(content.size())
        else:
            content_neighbour = node.content_neighbour.get(content.identifier)
            if content_neighbour != None:
                node.cache_metrics.track_request_neighbour()
                if self.nodes[content_neighbour].has(content.identifier):
                    node.cache_metrics.track_request_neighbour_success(content.size())
                    node.cache_metrics.track_hit(content.size())
                    if not self.outsource_resources:
                        node.store(content.identifier, content, at_timestamp)
                    return
                else:
                    node.content_neighbour[content.identifier] = None

            latest_nodes = self.find_latest_nodes(for_user, for_node, content_neighbour)

            for neighbour in latest_nodes:
                node.cache_metrics.track_request_neighbour()
                if self.nodes[neighbour].has(content.identifier):
                    node.content_neighbour[content.identifier] = neighbour
                    node.cache_metrics.track_request_neighbour_success(content.size())
                    node.cache_metrics.track_hit(content.size())
                    if not self.outsource_resources:
                        node.store(content.identifier, content, at_timestamp)
                    return

            node.cache_metrics.track_miss()
            node.cache_metrics.track_request_origin()
            node.store(content.identifier, content, at_timestamp)
            node.cache_metrics.track_bytes_origin(content.size())

    def find_latest_nodes(self, user, node, content_neighbour) -> list[str]:
        return [ x for x in self.__latest_n_nodes(self.node_trail_length, user)
                             if x != content_neighbour and x != node ]

    def __latest_n_nodes(self, n: int, for_user: str) -> list[str]:
        # We shift the last n nodes to exclude the currently connected node.
        return list(set(self.user_node_map[for_user][-(n+1):-1]))
