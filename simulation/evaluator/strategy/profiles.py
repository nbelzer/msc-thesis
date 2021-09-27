from simulation.evaluator.cache.cache_item import CacheItem
from simulation.evaluator.cache.profile_lru_cache import ProfileLRUCache
from simulation.evaluator.strategy.strategy import CacheStrategy
from collections import defaultdict
from simulation.evaluator.cache.profile_lru_cache import UserProfile

class ProfilesStrategy(CacheStrategy):
    profiles: dict[str, UserProfile]
    iteration: int = 0
    ranking_timeout: int = 5

    def __init__(self, nodes: dict[str, dict[str, any]], ranking_timeout: int = 5, profile_size: int = 1000):
        super().__init__({ name: self.build_node(settings)
                           for name, settings in nodes.items() })
        self.profiles = defaultdict(lambda: UserProfile(max_size=profile_size))
        self.iteration = 0
        self.ranking_timeout = ranking_timeout

    def build_node(self, from_settings: dict[str, any]) -> ProfileLRUCache:
        return ProfileLRUCache(capacity=int(from_settings["capacity"]))

    def handle_iteration(self, iteration: int):
        self.iteration = iteration
        if self.iteration % self.ranking_timeout == 0:
            for node in self.nodes.values():
                node.update_ranking({ user: profile for user, profile in self.profiles.items()
                                      if user in node.connected_profiles })

    def handle_node_connect(self, for_user: str, to_node: str):
        super().handle_node_connect(for_user, to_node)
        self.nodes[to_node].connected_profiles.add(for_user)

    def handle_node_disconnect(self, for_user: str):
        from_node = self.user_node_map[for_user][-1]
        self.profiles[for_user].last_connected_node = from_node
        self.nodes[from_node].connected_profiles.remove(for_user)

    def handle_request(self, for_user: str, for_node: str, content: CacheItem, at_timestamp: int):
        self.profiles[for_user].track(content.identifier)
        node = self.nodes[for_node]

        if node.retrieve(content.identifier, at_timestamp) != None:
            node.cache_metrics.track_hit(content.size())
            return

        neighbour = node.content_neighbour.get(content.identifier, None)
        if neighbour != None:
            node.cache_metrics.track_request_neighbour()
            if self.nodes[neighbour].has(content.identifier):
                node.cache_metrics.track_request_neighbour_success(content.size())
                node.cache_metrics.track_hit(content.size())
                node.store(content.identifier, content)
                return
            else:
                node.content_neighbour[content.identifier] = None

        rank = node.ranking.get(content.identifier, None)
        if rank != None:
            neighbours = [ self.profiles[user].last_connected_node for user in rank.by_users ]
            for n in [ n for n in neighbours if n != None and n != for_node ]:
                node.cache_metrics.track_request_neighbour()
                if self.nodes[n].has(content.identifier):
                    node.content_neighbour[content.identifier] = n
                    node.cache_metrics.track_request_neighbour_success(content.size())
                    node.cache_metrics.track_hit(content.size())
                    node.store(content.identifier, content)
                    return

        node.cache_metrics.track_miss()
        node.cache_metrics.track_request_origin()
        node.store(content.identifier, content)
        node.cache_metrics.track_bytes_origin(content.size())
