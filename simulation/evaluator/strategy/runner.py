from simulation.evaluator.strategy.strategy import CacheStrategy
from simulation.evaluator.cache.cache_item import CacheItem
from simulation.evaluator.instruction_parser import TraceIterator
import simulation.evaluator.instructions as ins
from simulation.evaluator.statistics.file_writer import StatsFileWriter, CacheMetrics
from collections import defaultdict

class StrategyRunner:
    strategy: CacheStrategy
    instructions: TraceIterator
    content_map: dict[str, int]
    stats_writers: dict[str, StatsFileWriter]

    def __init__(self, strategy: CacheStrategy, instructions: TraceIterator, content_map: dict[str, int], stats_writers: dict[str, StatsFileWriter]):
        self.strategy = strategy
        self.instructions = instructions
        self.instructions.reset()
        self.content_map = content_map
        self.stats_writers = stats_writers

    def perform(self):
        timestamp = 0
        iteration = 0
        node_stats: dict[str, list[CacheMetrics]] = defaultdict(list)
        for i in self.instructions:
            if isinstance(i, ins.RequestInstruction):
                identifier = i.identifier
                if identifier in self.content_map:
                    item = CacheItem(identifier=identifier, byte_size=self.content_map[identifier], last_accessed=-1)
                    self.strategy.handle_request(i.user_id, i.node_id, item, at_timestamp=timestamp)
            if isinstance(i, ins.ConnectInstruction):
                self.strategy.handle_node_connect(i.user_id, i.node_id)
            if isinstance(i, ins.DisconnectInstruction):
                self.strategy.handle_node_disconnect(i.user_id)
            if isinstance(i, ins.SetIterationInstruction):
                iteration = i.iteration
                self.strategy.handle_iteration(iteration)
            if isinstance(i, ins.CollectStatisticsInstruction):
                for node, stats in self.strategy.capture_statistics().items():
                    node_stats[node].append(stats)
                    self.__write_stats(node, iteration, stats)
            timestamp += 1
        return node_stats

    def __write_stats(self, for_node: str, iteration: int, stats: CacheMetrics):
        self.stats_writers[for_node].write_stats(iteration, stats)
