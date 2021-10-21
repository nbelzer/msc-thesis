from .finite_cache import FiniteCache, NotEnoughCapacityError
from .cache_item import CacheItem
from .linked_list import LinkedList
from collections import defaultdict
from typing import Optional

class LRUCache(FiniteCache):
    req_count: dict[str, int]
    min_req_count: int
    last_accessed: LinkedList

    def __init__(self, capacity: int, min_req_count: int = 3):
        super().__init__(capacity)
        self.req_count = defaultdict(int)
        self.last_accessed = LinkedList()
        self.min_req_count = min_req_count

    def retrieve(self, identifier: str, at_timestamp: int) -> Optional[CacheItem]:
        content = super().retrieve(identifier, at_timestamp)
        if content != None:
            self.last_accessed.append(identifier)
        return content

    def store(self, identifier: str, content: CacheItem, at_timestamp: int):
        if content.size() > self.capacity:
            # Only store items that fit in the cache.
            return

        self.req_count[identifier] += 1
        if self.req_count[identifier] < self.min_req_count:
            # Only store items with the minimum required request count.
            return

        # Once inserted the request count resets.
        del self.req_count[identifier]

        if not self.content_fits(content):
            self.remove_least_recently_used(content.size())
        super().store(identifier, content)
        self.last_accessed.append(identifier)


    def remove_least_recently_used(self, no_bytes: int):
        """Remove items in the order of least recently used.

        The `no_bytes` determines how many bytes need to be freed up, and
        therefore how many items will be removed.  Cannot free up more than the
        capacity of the node."""
        if no_bytes > self.capacity:
            raise NotEnoughCapacityError(f"Cannot free more bytes ({no_bytes}) than the total capacity ({self.capacity}.)")

        bytes_freed = self.capacity_available()
        while bytes_freed < no_bytes:
            try:
                to_remove = self.content[self.last_accessed.pop()]
            except IndexError as e:
                print(f"Tried to free {no_bytes}, but couldn't find any more items.")
                print(f"{self.content}")
            self.remove(to_remove.identifier)
            bytes_freed = self.capacity_available()
