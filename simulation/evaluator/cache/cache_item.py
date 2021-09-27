from dataclasses import dataclass

@dataclass
class CacheItem:
    identifier: str
    byte_size: int
    last_accessed: int

    def size(self):
        return self.byte_size
