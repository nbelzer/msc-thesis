from .lru_cache_linked import LRUCache

class CooperativeLRUCache(LRUCache):
    content_neighbour: dict[str, str]

    def __init__(self, capacity: int):
        super().__init__(capacity)
        self.content_neighbour = {}
