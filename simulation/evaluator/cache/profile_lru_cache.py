from .finite_cache import FiniteCache
from typing import Optional
from dataclasses import dataclass, field
from .cache_item import CacheItem

@dataclass
class ProfileRanking:
    popularity: int = 0
    by_users: set[str] = field(default_factory=set)

@dataclass
class UserProfile:
    max_size: int
    resources: list[str] = field(default_factory=list)
    last_connected_node: Optional[str] = None

    def track(self, identifier: str):
        """Store this resource in the profile, removing the last item if the profile reached max size, not checked for duplicates."""
        self.resources.append(identifier)
        if len(self.resources) > self.max_size:
            self.resources.pop()


class ProfileLRUCache(FiniteCache):
    connected_profiles: set[str]
    content_neighbour: dict[str, str]
    ranking: dict[str, ProfileRanking]

    def __init__(self, capacity: int):
        super().__init__(capacity)
        self.content_neighbour = {}
        self.connected_profiles = set([])
        self.ranking = {}

    def store(self, identifier: str, content: CacheItem):
        if not self.content_fits(content):
            rank = self.ranking.get(content.identifier, None)
            # Give the lowest popularity by default and try to make enough space.
            popularity = 0
            if rank != None:
                # Set actual popularity if in ranking.
                popularity = rank.popularity

            if self.remove_older_items(content.size(), popularity) == False:
                # Don't try to store the item if there are not enough
                # items to remove with a lower ranking.
                return

        super().store(identifier, content)

    def remove_older_items(self, no_bytes: int, less_popular_than: int):
        bytes_freed = self.capacity_available()

        # As self.ranking is sorted we do not need to sort this array.
        content_by_least_accessed = []

        for k in self.content:
            if k not in self.ranking:
                # Make space by removing items that are not in the ranking.
                content_by_least_accessed.append(k)

        for k in self.ranking.keys():
            if self.ranking[k].popularity > less_popular_than:
                # Break the for loop early if the last_accessed items
                # are above the older_than threshold, this is possible
                # because the ranking is pre-sorted.
                break
            if k in self.content:
                content_by_least_accessed.append(k)

        available_bytes = sum([ self.content[k].size() for k in content_by_least_accessed ])
        if bytes_freed + available_bytes < no_bytes:
            return False

        while bytes_freed < no_bytes:
            # Only remove the least recently used items to make the
            # minimum of space available.
            to_remove = self.content[content_by_least_accessed.pop(0)]
            self.remove(to_remove.identifier)
            bytes_freed += to_remove.size()
        return True


    def update_ranking(self, profiles: dict[str, UserProfile]):
        ranking = {}
        for user, profile in profiles.items():
            for identifier in profile.resources:
                if identifier not in ranking:
                    ranking[identifier] = ProfileRanking()
                rank = ranking[identifier]
                rank.popularity += 1
                rank.by_users.add(user)

        self.ranking = dict(sorted(ranking.items(), key=lambda x: x[1].popularity))
