from dataclasses import dataclass
from typing import Callable, Optional
import json
import random
from tqdm import tqdm
import argparse
import pathlib
import gzip
from .main_zipf import EdgeNode
from .page_visitor import PageVisitor
from .confined_list import ConfinedList
from .node_visitor import NodeVisitor
from .timeout_behaviour import TimeoutBehaviour
from .utils import Page, read_page_map

@dataclass
class UserConfiguration:
    specialisations: list[str]
    move_behaviour: Callable[..., bool]
    jump_behaviour: Callable[..., bool]


class User(PageVisitor, NodeVisitor, TimeoutBehaviour):
    """Represents a user object."""
    identifier: str
    config: UserConfiguration

    def __init__(self, identifier: str, starting_node: EdgeNode, config: UserConfiguration):
        self.current_timeout = 0
        self.current_node = starting_node
        self.current_page = None
        self.node_history = ConfinedList()
        self.page_history = ConfinedList()
        self.identifier = identifier
        self.config = config

    def next_iteration(self):
        self.decrement_timeout()

    def should_move(self) -> bool:
        return self.config.move_behaviour()

    def should_jump(self) -> bool:
        if self.current_page == None:
            return True
        return self.config.jump_behaviour()

    def connect_to(self, new_node: EdgeNode):
        self.set_current_node(new_node)

    def can_visit(self) -> bool:
        return not self.has_timeout()

    def visit_page(self, new_page: Page):
        if not self.can_visit():
            return
        self.set_current_page(new_page)

@dataclass
class UserTraceConfig:
    node_map: dict[str, EdgeNode]
    no_users: int = 500
    user_subset_size: float = 0.1
    no_iterations: int = 1000
    move_chance: float = 0.05
    jump_chance: float = 0.10
    max_timeout: int = 12
    seed: Optional[str] = None

    def to_filename(self) -> str:
        return f"{self.no_users}users-{len(self.node_map)}nodes-{self.no_iterations}its-subset-fraction{self.user_subset_size}-move{self.move_chance}-jump{self.jump_chance}-timeout{self.max_timeout}-{self.seed}"

def one_every(random, x: int):
    return lambda _: random.random() <= 1.0/x

def for_fraction(random, frac: float):
    return lambda _: random.random() <= frac

def subset_of(content, filter_func):
    return filter(filter_func, content)

class UserSimulation:
    config: UserTraceConfig
    random: random.Random
    page_map: dict[str, Page]
    resource_map: dict[str, int]
    pages: list[str]
    cumulative_weights: list[float]

    def __init__(self, config: UserTraceConfig, page_map_file: str):
        self.config = config
        self.random = random.Random()
        self.random.seed(a=config.seed)
        self.page_map = read_page_map(page_map_file)
        self.pages = list(set(self.page_map.keys()))

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

    def __create_user_move_behaviour(self):
        return lambda: self.random.random() <= self.config.move_chance

    def __create_user_jump_behaviour(self):
        return lambda: self.random.random() <= self.config.jump_chance

    def __setup_user(self, identifier: str, starting_node: EdgeNode) -> User:
        config = UserConfiguration(
            specialisations=list(subset_of(self.page_map.keys(), filter_func=for_fraction(self.random, self.config.user_subset_size))),
            jump_behaviour=self.__create_user_jump_behaviour(),
            move_behaviour=self.__create_user_move_behaviour())
        user = User(identifier=identifier, starting_node=starting_node, config=config)
        user.current_timeout = self.random.randint(0, self.config.max_timeout)
        return user

    def __simulate_user_movement(self, user: User) -> list[str]:
        if user.should_move() and len(user.next_nodes()) > 0:
            old_node = user.current_node
            new_node = self.random.choice(user.next_nodes())
            user.connect_to(self.config.node_map[new_node])
            return [ f"DCN {user.identifier} {old_node.identifier}", f"CON {user.identifier} {new_node}" ]
        return []

    def __simulate_user_page_visit(self, user: User) -> list[str]:
        if user.can_visit():
            if user.should_jump():
                new_page = self.random.choice(user.config.specialisations)
            else:
                new_page = self.random.choice(user.next_pages())
            while new_page not in self.page_map:
                new_page = self.random.choice(user.config.specialisations)
            user.visit_page(self.page_map[new_page])
            user.current_timeout = self.random.randint(0, self.config.max_timeout)
            return [ f"REQ {user.identifier} {user.current_node.identifier} {r}" for r in self.page_map[new_page].resources ]
        return []

    def __simulate_user_iteration(self, user: User) -> list[str]:
        actions = []
        user.next_iteration()
        actions.extend(self.__simulate_user_movement(user))
        actions.extend(self.__simulate_user_page_visit(user))
        return actions


if __name__ == "__main__":
    """Generates a set of traces for a given amount of users, iterations,
    and edge nodes.
    """
    parser = argparse.ArgumentParser(description="Simulate a set of users requesting content from a page-map while moving over a node-map.")
    parser.add_argument('page_map', type=pathlib.Path,
                        help="The location of the page-map.")
    parser.add_argument('node_map', type=pathlib.Path,
                        help="A (json) map on how users can move between nodes.")
    parser.add_argument('--out-file', type=pathlib.Path, default='./example.trace.gz',
                        help="The output location of the trace file, recommended file format is <name>.trace.gz")
    parser.add_argument('--no-iterations', type=int, default=50)
    parser.add_argument('--no-users', type=int, default=10)
    parser.add_argument('--seed', type=str, default='',
                        help="The seed used by the random generator")
    parser.add_argument('--max-timeout', type=int, default=12,
                        help="The maximum timeout after a content request (in iterations).")
    parser.add_argument('--user-subset-size', type=float, default=0.1,
                        help="The size of the subset fraction each user will be able to access.")
    parser.add_argument('--jump-chance', type=float, default=0.1,
                        help="How likely is the user to jump to different content in a range of (never) [0, 1.0] (every iteration)")
    parser.add_argument('--move-chance', type=float, default=0.05,
                        help="How likely is the user to move to a different edge node in a range of (never) [0, 1.0] (every iteration)")

    args = parser.parse_args()
    no_iterations = args.no_iterations
    no_users = args.no_users
    max_timeout = args.max_timeout
    user_subset_size = args.user_subset_size
    jump_chance = args.jump_chance
    move_chance = args.move_chance
    page_map_file = args.page_map
    node_map_file = args.node_map

    with open(node_map_file, "r") as node_map:
        data = json.load(node_map)
        node_map = { i: EdgeNode(identifier=i, neighbours=n) for
                     i, n in data["nodes"].items() }

    config = UserTraceConfig(node_map=node_map, no_users=no_users, user_subset_size=user_subset_size, no_iterations=no_iterations, move_chance=move_chance, jump_chance=jump_chance, max_timeout=max_timeout, seed=args.seed)
    simulation = UserSimulation(config, args.page_map_file)
    with gzip.open(args.out_file, 'wb') as f:
        f.write(str.encode(""))
        for action in simulation.simulate():
            f.write(str.encode(f"{action}\n"))
