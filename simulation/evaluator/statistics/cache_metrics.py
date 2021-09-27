from dataclasses import dataclass

@dataclass
class CacheMetrics:
    no_items: int = 0
    hits: int = 0
    misses: int = 0
    bytes_used: int = 0
    cache_bytes: int = 0
    origin_bytes: int = 0
    neighbour_bytes: int = 0
    requests_to_neighbours: int = 0
    requests_to_neighbours_success: int = 0
    requests_to_origin: int = 0

    def track_item_stored(self, no_bytes: int):
        self.no_items += 1
        self.bytes_used += no_bytes

    def track_item_removed(self, no_bytes: int):
        self.no_items -= 1
        self.bytes_used -= no_bytes

    def track_hit(self, no_bytes: int):
        self.hits += 1
        self.cache_bytes += no_bytes

    def track_miss(self):
        self.misses += 1

    def track_bytes_origin(self, no_bytes: int):
        self.origin_bytes += no_bytes

    def track_request_origin(self):
        self.requests_to_origin += 1

    def track_request_neighbour(self):
        self.requests_to_neighbours += 1

    def track_request_neighbour_success(self, no_bytes: int):
        self.requests_to_neighbours_success += 1
        self.neighbour_bytes += no_bytes

    def total_requests(self):
        return self.hits + self.misses

    def total_bytes(self):
        return self.cache_bytes + self.origin_bytes
