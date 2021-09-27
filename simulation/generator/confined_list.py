class EmptyListException(Exception):
    pass

class ConfinedList:
    """A list that can hold a limited set of items."""
    max_items: int
    _list: list[any]

    def __init__(self, max_items: int = 5):
        self.max_items = max_items
        self._list = list()

    def push(self, value):
        """Append an item, removing the oldest item in the list if `max_items`
        has been reached.
        """
        while len(self._list) >= self.max_items:
            del self._list[0]
        self._list.append(value)

    def pop(self):
        """Remove and return the last added item."""
        if len(self._list) == 0:
            return EmptyListException()
        latest_item = self._list[-1]
        del self._list[-1]
        return latest_item

    def latest_item(self):
        """Return the last added item."""
        if len(self._list) == 0:
            return EmptyListException()
        return self._list[-1]

    def to_list(self):
        """Return a copy of the current state of the list."""
        return list(self._list)

    def __len__(self):
        return self._list.__len__()
