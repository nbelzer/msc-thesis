from dataclasses import dataclass
from typing import Optional

@dataclass
class Node:
    data: any
    previous: Optional[any]
    next: Optional[any]

@dataclass
class LinkedList:
    """LinkedList Adaptation for LRU caches."""
    head: Optional[Node]
    tail: Optional[Node]
    mapping: dict[any, Node]

    def __init__(self):
        self.head = None
        self.tail = None
        self.mapping = {}

    def append(self, data):
        if self.head != None and self.head.data == data:
            return
        if data in self.mapping:
            node = self.mapping[data]
            if node.previous != None:
                node.previous.next = node.next
            if node.next != None:
                node.next.previous = node.previous
            else:
                # This was the tail.
                self.tail = node.previous
            node.previous = None
        else:
            node = Node(data=data, previous=None, next=None)
            self.mapping[data] = node
        if self.head != None:
            node.next = self.head
            self.head.previous = node
        self.head = node
        if self.tail == None:
            self.tail = node

    def pop(self):
        if self.tail != None:
            last_elem = self.tail
            self.tail = last_elem.previous
            if self.head.data == last_elem.data:
                self.head = None
        elif self.head != None:
            last_elem = self.head
            self.head = None
        else:
            return None
        if last_elem.previous != None:
            last_elem.previous.next = None

        del self.mapping[last_elem.data]
        return last_elem.data

l = LinkedList()
# l.append('Test')
# assert l.pop() == 'Test'

# l.append('Hi')
# l.append('There')
# l.append('You')
# assert l.pop() == 'Hi'
# l.append('There')
# assert l.pop() == 'You'
# assert l.pop() == 'There'

# l.append("Hello")
# l.append("World")
# l.append("Hello")
# assert l.pop() == "World"
# assert l.pop() == "Hello"

# l.append('Hi')
# l.append('There')
# l.append('You')
# l.append('There')
# assert l.pop() == 'Hi'
# assert l.pop() == 'You'
# l.append("Doe")
# assert l.pop() == 'There'
# l.append("John")
# l.append("John")
# assert l.pop() == 'Doe'
# assert l.pop() == 'Doe'
