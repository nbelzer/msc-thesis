from .cache import Cache
from .cache_item import CacheItem

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class NotEnoughCapacityError(Error):
    """Exception raised when the file size is larger than cache capacity."""
    pass

class FiniteCache(Cache):
    capacity: int

    def __init__(self, capacity: int):
        super().__init__()
        self.capacity = capacity

    def capacity_available(self):
        return self.capacity - self.capacity_used

    def content_fits(self, content: CacheItem):
        return self.capacity_available() >= content.size()

    def store(self, identifier: str, content: CacheItem):
        if self.content_fits(content):
            super().store(identifier, content)
        else:
            raise NotEnoughCapacityError()
