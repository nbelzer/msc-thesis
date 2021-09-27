from typing import Optional
from simulation.evaluator.statistics.cache_metrics import CacheMetrics
from .cache_item import CacheItem

class Cache:
    content: dict[str, CacheItem] = {}
    cache_metrics: CacheMetrics
    capacity_used: int = 0

    def __init__(self):
        self.content = {}
        self.cache_metrics = CacheMetrics()
        self.capacity_used = 0

    def store(self, identifier: str, content: CacheItem):
        if identifier in self.content:
            return
        self.capacity_used += content.size()
        self.cache_metrics.track_item_stored(content.size())
        self.content[identifier] = content


    def retrieve(self, identifier: str, at_timestamp: int) -> Optional[CacheItem]:
        """Try to retrieve content from the cache by identifier.

        Returns content stored under the given `identifier` if stored,
        tracks metrics on this object like `misses`, `hits`, and
        `bytes_saved`, and updates the `last_accessed` property on the
        content.

        """
        content = self.content.get(identifier)
        if content == None:
            return None
        content.last_accessed = at_timestamp
        return content

    def retrieve_no_metrics(self, identifier):
        """Try to retrieve content from the cache by identifier without tracking
        metrics.

        Returns content stored under the given `identifier` if stored
        without tracking or updating any metrics.  Should only be used
        if you want the retrieval not to influence the metrics or future
        caching decisions.

        """
        if self.has(identifier):
            return self.content[identifier]
        return None

    def remove(self, identifier):
        if not self.has(identifier):
            print(f"Trying to remove item that is not in the cache: {identifier}")
            return
        item = self.content[identifier]
        self.capacity_used -= item.size()
        self.cache_metrics.track_item_removed(item.size())
        del self.content[identifier]

    def has(self, identifier):
        return identifier in self.content
