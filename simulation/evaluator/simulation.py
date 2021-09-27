from dataclasses import dataclass
from dataclasses import field

@dataclass
class User:
    identifier: str
    connected_node_id: str
    node_history: list[str] = field(default_factory=list)

    def last_nodes(self, n: int=5):
        return reversed(self.node_history[-n:])


class SimulationContext:
    iteration: int
    nodes: list[str]
    users: dict[str, User]

    def __init__(self, nodes: list[str] = []):
        self.iteration = 0
        self.nodes = nodes
        self.users = {}

    def get_user(self, identifier):
        return self.users.get(identifier, User(identifier=identifier, connected_node_id=-1))

    def store_user(self, user):
        self.users[user.identifier] = user
