from .cache_metrics import CacheMetrics
import dataclasses
import pathlib

class StatsFileWriter:
    file_path: pathlib.Path
    separator: str = ";"
    header_items = [ "iteration", "hits", "misses", "no_items", "bytes_used", "cache_bytes", "origin_bytes", "neighbour_bytes", "requests_to_origin", "requests_to_neighbours", "requests_to_neighbours_success" ]

    def __init__(self, file_path: pathlib.Path):
        self.file_path = file_path
        with open(self.file_path, 'w') as f:
            f.write(f"{self.__header_line()}\n")

    def write_stats(self, iteration: int, stats: CacheMetrics):
        values = dataclasses.asdict(stats)
        stats_items = [ iteration] + [ values[key] for key in self.header_items
                                       if key != "iteration" ]
        stats_line = self.separator.join(str(x) for x in stats_items )
        with open(self.file_path, 'a') as f:
            f.write(f"{stats_line}\n")

    def __header_line(self):
        return self.separator.join(self.header_items)
