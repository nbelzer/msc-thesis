from dataclasses import dataclass
from typing import Callable, Optional
import json
import random
from tqdm import tqdm
import argparse
import pathlib
import gzip
from .utils import read_resource_map
from .node_visitor import NodeVisitor
from .confined_list import ConfinedList
from .edge_graph import EdgeNode

def zipf(rank, exponent=1.0):
    """Returns the relative frequency of the content at the given rank
    compared to the first."""
    return 1 / pow(rank, exponent)

@dataclass
class UserConfiguration:
    move_behaviour: Callable[..., bool]

class User(NodeVisitor):
    """Represents a user object."""
    identifier: str
    config: UserConfiguration

    def __init__(self, identifier: str, starting_node: EdgeNode, config: UserConfiguration):
        self.current_node = starting_node
        self.node_history = ConfinedList()
        self.identifier = identifier
        self.config = config

    def next_iteration(self):
        pass

    def should_move(self) -> bool:
        return self.config.move_behaviour()

    def connect_to(self, new_node: EdgeNode):
        self.set_current_node(new_node)

@dataclass
class TraceConfig:
    node_map: dict[str, EdgeNode]
    no_users: int = 500
    no_iterations: int = 1000
    zipf_exponent: float = 0.75
    move_chance: float = 0.05
    seed: Optional[str] = None

    def to_filename(self) -> str:
        return f"{self.no_users}users-{len(self.node_map)}nodes-{self.no_iterations}its-zipf-{self.zipf_exponent}-move-chance-{self.move_chance}-{self.seed}"


def weights_to_cum_weights(weights: list[float]) -> list[float]:
    total_weight = 0
    cum_weights = []
    for w in weights:
        total_weight += w
        cum_weights.append(total_weight)
    return cum_weights

def cumulative_weights_for(no_items: int = 1, zipf_exponent: float = 1.0):
    weights = [ zipf(rank + 1, exponent=zipf_exponent) for rank in range(no_items) ]
    return weights_to_cum_weights(weights)

class Simulation:
    config: TraceConfig
    random: random.Random
    resource_map: dict[str, int]
    resources: list[str]
    cumulative_weights: list[float]

    def __init__(self, config: TraceConfig, resource_map_file: str):
        self.config = config
        self.random = random.Random()
        self.random.seed(a=config.seed)
        self.resource_map = read_resource_map(resource_map_file)
        self.resources = list(set(self.resource_map.keys()))
        self.random.shuffle(self.resources)
        self.cumulative_weights = cumulative_weights_for(no_items=len(self.resources), zipf_exponent=self.config.zipf_exponent)

    def simulate(self) -> list[str]:
        """Generate a set of actions for the supplied `TraceConfig`."""
        starting_locations = [ self.random.choice(list(self.config.node_map.values()))
                               for i in range(self.config.no_users) ]
        users = [ self.__setup_user(i, starting_node)
                  for i, starting_node in enumerate(starting_locations) ]

        actions = [ f"CON {i} {loc.identifier}"
                          for i, loc in enumerate(starting_locations) ]
        del starting_locations

        print(f"Simulating {self.config.no_iterations} iterations for {self.config.no_users} users.")
        for i in tqdm(range(self.config.no_iterations)):
            actions.append(f"ITERATION {i}")
            for user in users:
                actions.extend(self.__simulate_user_iteration(user))
            actions.append(f"GET_STATS")

        return actions

    def __create_user_move_behaviour(self, likelihood: float = 0.05):
        return lambda: self.random.random() <= likelihood

    def __setup_user(self, identifier: str, starting_node: EdgeNode) -> User:
        config = UserConfiguration(
            move_behaviour=self.__create_user_move_behaviour(likelihood=self.config.move_chance))
        user = User(identifier=identifier, starting_node=starting_node, config=config)
        return user

    def __simulate_user_movement(self, user: User):
        if user.should_move() and len(user.next_nodes()) > 0:
            old_node = user.current_node
            new_node = self.random.choice(user.next_nodes())
            user.connect_to(self.config.node_map[new_node])
            return [ f"DCN {user.identifier} {old_node.identifier}", f"CON {user.identifier} {new_node}" ]
        return []

    def __simulate_user_requests(self, user: User):
        return [ f"REQ {user.identifier} {user.current_node.identifier} {r}"
                 for r in self.__pick_resources(no_resources=1) ]

    def __simulate_user_iteration(self, user: User):
        actions = []
        user.next_iteration()
        actions.extend(self.__simulate_user_movement(user))
        actions.extend(self.__simulate_user_requests(user))
        return actions

    def __pick_resources(self, no_resources: int = 1) -> str:
        return self.random.choices(self.resources, cum_weights=self.cumulative_weights, k=no_resources)


if __name__ == "__main__":
    """Generates a set of traces for a given amount of users, iterations,
    and edge nodes.
    """
    parser = argparse.ArgumentParser(description="Simulate a set of users requesting content from a page-map while moving over a node-map.")
    parser.add_argument('resource_map', type=pathlib.Path,
                        help="The location of the resource-map.")
    parser.add_argument('node_map', type=pathlib.Path,
                        help="A (json) map on how users can move between nodes.")
    parser.add_argument('--out-file', type=pathlib.Path, default='./example.trace.gz',
                        help="The output location of the trace file, recommended file format is <name>.trace.gz")
    parser.add_argument('--no-iterations', type=int, default=50)
    parser.add_argument('--no-users', type=int, default=10)
    parser.add_argument('--seed', type=str, default='',
                        help="The seed used by the random generator")
    parser.add_argument('--zipf-exponent', type=float, default=0.8,
                        help="The zipf exponent used (default is 0.8).")
    parser.add_argument('--move-chance', type=float, default=0.05,
                        help="How likely is the user to move to a different edge node in a range of (never) [0, 1.0] (every iteration)")

    args = parser.parse_args()
    resource_map_file = args.resource_map
    node_map_file = args.node_map

    with open(node_map_file, "r") as node_map:
        data = json.load(node_map)
        node_map = { i: EdgeNode(identifier=i, neighbours=n) for
                     i, n in data["nodes"].items() }

    config = TraceConfig(no_iterations=args.no_iterations, no_users=args.no_users, seed=args.seed, move_chance=args.move_chance, node_map=node_map, zipf_exponent=args.zipf_exponent)
    simulation = Simulation(config, args.resource_map)

    with gzip.open(args.out_file, 'wb') as f:
        f.write(str.encode(""))
        for action in simulation.simulate():
            f.write(str.encode(f"{action}\n"))
