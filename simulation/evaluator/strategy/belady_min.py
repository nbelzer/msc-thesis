import pathlib
import argparse
from typing import Tuple
from collections import defaultdict
from simulation.evaluator.instruction_parser import TraceIterator
from simulation.evaluator.instructions import RequestInstruction, SetIterationInstruction
from simulation.generator.utils import read_resource_map
import sys
from bisect import bisect_right
from simulation.evaluator.statistics.cache_metrics import CacheMetrics
from simulation.evaluator.statistics.file_writer import StatsFileWriter

def find_gt(a, x):
    """Find leftmost value greater than x using bisect, only works for a
    sorted array, for more information see:

    https://docs.python.org/3.6/library/bisect.html

    """
    i = bisect_right(a, x)
    if i != len(a):
        return a[i]
    raise ValueError


class BeladyOracle:
    requests_for: dict[str, list[int]]

    def __init__(self, requests_for: dict[str, list[int]]):
        self.requests_for = requests_for

    def calls_for(self, identifier):
        return self.requests_for.get(identifier)

    def next_call_for(self, identifier, current_timestamp):
        calls = self.calls_for(identifier)
        try:
            return find_gt(calls, current_timestamp)
        except ValueError:
            return sys.maxsize

    @staticmethod
    def from_ordered_list(request_list: list[str]):
        request_by_iteration = defaultdict(list)
        for i, request in enumerate(request_list):
            request_by_iteration[request].append(i)
        return BeladyOracle(requests_for=request_by_iteration)


class UnableToStoreError(Exception):
    pass

class BeladysMIN:
    no_requests: int = 0
    max_weight: int
    used_weight: int = 0

    stored: dict[str,int] = {}

    def __init__(self, max_weight: int):
        self.max_weight = max_weight
        self.used_weight = 0
        self.no_requests = 0
        self.stored = {}

    def weight_for(self, identifier) -> int:
        raise NotImplementedError

    def next_call_for(self, identifier) -> int:
        raise NotImplementedError

    def store_item(self, identifier):
        weight = self.weight_for(identifier)
        self.stored[identifier] = self.next_call_for(identifier)
        self.used_weight += weight

    def ranking_by_next_call(self, min_iteration: int = 0):
        """Generate a ranknig of `stored` identifiers sorted by the next
        time they will be called (from early-last).
        """
        return list(map(lambda x: x[0],
            sorted([ (k, v) for k, v in self.stored.items() if v > min_iteration ],
                   key=lambda x: x[1])))

    def make_weight_available(self, weight: int, min_iteration: int = 0) -> list[str]:
        """Make sure a certain amount of weight is available to use.
        """
        if weight > self.max_weight:
            raise UnableToStoreError("Trying to clear weight for an item that will not fit.")
        if self.__can_store(weight):
            return []
        ranking_by_call = self.ranking_by_next_call(min_iteration=min_iteration)
        if weight > sum([ self.weight_for(item) for item in ranking_by_call ]):
            raise UnableToStoreError("Not enough items to evict")
        evicted = []
        while not self.__can_store(weight):
            item_to_evict = ranking_by_call.pop()
            evicted.append(self.evict_item(item_to_evict))
        return evicted


    def evict_item(self, item_to_evict: str) -> str:
        """Evict a specific item from the stored items.

        Evicting an item releases the weight that this item occupied.
        """
        del self.stored[item_to_evict]
        self.used_weight -= self.weight_for(item_to_evict)
        return item_to_evict


    def handle_request(self, identifier) -> Tuple[str, list[str]]:
        """Handles a single request.

        Returns the items that were evicted to store this item.

        """
        if identifier in self.stored:
            self.no_requests += 1
            self.stored[identifier] = self.next_call_for(identifier)
            return "HIT", []

        item_weight = self.weight_for(identifier)
        try:
            evicted = self.make_weight_available(item_weight, min_iteration=self.next_call_for(identifier))
        except UnableToStoreError as e:
#            print(e)
            self.no_requests += 1
            return "PASS", []

        self.store_item(identifier)
        self.no_requests += 1
        return "MISS", evicted

    def __available_weight(self):
        return self.max_weight - self.used_weight

    def __can_store(self, weight):
        if weight > self.max_weight:
            raise UnableToStoreError(f"This item ({weight}b) is too large to store in this cache ({self.max_weight}b)")
        return weight <= self.__available_weight()


class BeladysMINIteration(BeladysMIN):
    """Wrapper class around Belady's MIN algorithm that uses iterations to
    be able to compare the performance against other strategies.

    "The most efficient caching algorithm would be to always discard the
    information that will not be needed for the longest time in the
    future."
    (en.wikipedia.org/wiki/Cache_replacement_policies#Bélády's_algorithm)

    """
    content_byte_size: dict[str, int]
    request_trace: dict[int, list[str]]
    oracle: BeladyOracle
    average_content_size: int

    def __init__(self, byte_capacity: int, request_trace: dict[int, list[str]], content_byte_size: dict[str, int], average_content_weight: int):
        """Initializes the wrapper around Belady's MIN algorithm

        The order of the requests in every entry in the `request_trace` matter.

        """
        super().__init__(byte_capacity)
        self.content_byte_size = content_byte_size
        self.request_trace = request_trace
        self.oracle = BeladyOracle.from_ordered_list([ request
                                                       for iteration in request_trace.values()
                                                       for request in iteration ])
        self.average_content_weight = average_content_weight

    def simulate(self, no_iterations: int, out_file: pathlib.Path):
        metrics = CacheMetrics()
        stats_writer = StatsFileWriter(out_file)
        for iteration in range(no_iterations):
            content = self.request_trace[iteration]
            for identifier in content:
                inserted, evicted = self.handle_request(identifier)
                content_weight = self.weight_for(identifier)
                if inserted == "MISS":
                    metrics.track_miss()
                    metrics.track_item_stored(content_weight)
                if inserted == "MISS" or inserted == "PASS":
                    metrics.track_request_origin()
                    metrics.track_bytes_origin(content_weight)
                if inserted == "HIT":
                    metrics.track_hit(content_weight)

                if evicted != None:
                    [ metrics.track_item_removed(self.weight_for(item)) for item in evicted ]

            stats_writer.write_stats(iteration, metrics)

    def weight_for(self, identifier):
        try:
            return self.content_byte_size[identifier]
        except KeyError:
            return self.average_content_weight

    def next_call_for(self, identifier):
        return self.oracle.next_call_for(identifier, self.no_requests)


def order_content_by_node(trace) -> Tuple[dict[str, dict[int, list[str]]], int]:
    content_by_node_by_iteration = defaultdict(lambda: defaultdict(list))
    iteration = 0
    for i in trace:
        if isinstance(i, SetIterationInstruction):
            iteration = i.iteration
        if isinstance(i, RequestInstruction):
            content_by_node_by_iteration[i.node_id][iteration].append(i.identifier)
    return content_by_node_by_iteration, iteration + 1

def run_belady(trace, resource_mapping: dict[str, int], cache_size: int, out_dir: str, marker: str = ""):
    if len(marker) > 0:
        marker = f"-{marker}"
    average_content_size = int(sum(resource_mapping.values()) / len(resource_mapping))
    content_by_node_by_iteration, no_iterations = order_content_by_node(trace)

    belady_by_node = { node_id: BeladysMINIteration(cache_size, content_by_iteration, resource_mapping, average_content_size)
                       for node_id, content_by_iteration in content_by_node_by_iteration.items() }

    for node_id, MIN in belady_by_node.items():
        # print(f"\nSimulating node {node_id}...")
        MIN.simulate(no_iterations, out_file=f"{out_dir}/{node_id}{marker}.csv")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create dataset plots')
    parser.add_argument('trace', type=pathlib.Path,
                        help='the location of trace file to evaluate')
    parser.add_argument('resources', type=pathlib.Path,
                        help='the location of a file mapping to content bytes')
    parser.add_argument('--node-capacity', type=int, default=512,
                        help='the amount of MB available for storage an each node')
    parser.add_argument('--out-dir', type=pathlib.Path, default="./belady-out/",
                        help='where to save the statistics')

    args = parser.parse_args()

    print("Analyzing file sizes...")
    resource_size = read_resource_map(args.resources)

    cache_size = args.node_capacity*1024*1024
    instructions = TraceIterator.from_file(args.trace)
    run_belady(instructions, resource_size, cache_size, args.out_dir)
