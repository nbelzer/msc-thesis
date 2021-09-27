from simulation.evaluator.instruction_parser import TraceIterator, InstructionParser, Instruction
import simulation.evaluator.instructions as ins
from simulation.generator.main_zipf import EdgeNode
from simulation.evaluator.statistics.file_writer import StatsFileWriter
import csv
import numpy as np
import os
import re
import gzip
import time
import copy
from typing import Tuple
import json
from experiments.stats_reader import load_file

class TraceIteratorProxy(TraceIterator):
    """A simple object that allows a trace for N amount of nodes to be used with a setup of N or less nodes by mapping the requests."""
    def __init__(self, instructions: list[Instruction], proxy_map: dict[str, str]):
        super().__init__([ TraceIteratorProxy.remap_node(i, proxy_map) for i in copy.deepcopy(instructions) ])

    @staticmethod
    def remap_node(instruction: Instruction, proxy_map: dict[str, str]):
        if isinstance(instruction, ins.RequestInstruction):
            instruction.node_id = proxy_map[instruction.node_id]
        if isinstance(instruction, ins.ConnectInstruction):
            instruction.node_id = proxy_map[instruction.node_id]
        if isinstance(instruction, ins.DisconnectInstruction):
            instruction.node_id = proxy_map[instruction.node_id]
        return instruction

class MultiRunData:
    """A helper object that allows easy creation of a mean-variance dataset by combining multiple datapoints."""
    datapoints: list[list[float]]

    def __init__(self):
        self.datapoints = []

    def add_run(self, run: list[float]):
        self.datapoints.append(run)

    def to_mean_variance(self):
        return [ calc_variance(list(x)) for x in zip(*self.datapoints) ]

def make_dir(dir) -> str:
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir

def __parse_actions(actions: list[str]) -> TraceIterator:
    return TraceIterator(InstructionParser.parse_all(actions))

def generate_trace(simulation) -> TraceIterator:
    """Generates a trace with the given parameters."""
    return __parse_actions(simulation.simulate())

def generate_trace_if_not_exists(identifier: str, simulation) -> list[str]:
    """Generates a trace if it doesn't exist yet."""
    if not os.path.exists(identifier):
        actions = simulation.simulate()
        with gzip.open(identifier, 'wb') as f:
            f.write(str.encode(""))
            for action in actions:
                f.write(str.encode(f"{action}\n"))
        return actions
    return None

def load_or_generate_trace(identifier: str, simulation) -> TraceIterator:
    """Loads the trace for the given `identifier`, if the trace does not exist it is generated according to the `simulation`."""
    actions = generate_trace_if_not_exists(identifier, simulation)
    if actions != None:
        return __parse_actions(actions)
    return TraceIterator.from_file(identifier)

def clean_identifier(identifier: str) -> str:
    """Removes all whitespaces from the identifier."""
    return re.sub(r'\s+', '', identifier)

def read_resource_map(from_file) -> dict[str, int]:
    resource_map = {}
    with open(from_file, 'r') as f:
        resource_reader = csv.DictReader(f, delimiter=';')
        for row in resource_reader:
            identifier = clean_identifier(row['identifier'])
            size = int(row['size'])
            if size > 0:
                resource_map[identifier] = size
    return resource_map


def read_node_map(from_file: str) -> dict[str, EdgeNode]:
    with open(from_file, 'r') as f:
        return { identifier: EdgeNode(identifier=identifier, neighbours=neighbours) for identifier, neighbours in json.loads(f.read())['nodes'].items() }

def setup_node_map(no_nodes: int) -> dict[str, EdgeNode]:
    nodes = [ f"cdn{i + 1}" for i, _ in enumerate(range(no_nodes)) ]
    return { node: EdgeNode(identifier=node, neighbours=[ n for n in nodes if n != node ])
             for node in nodes }

def setup_nodes(no_nodes: int, node_capacity: int):
    return {f"cdn{i + 1}": { "capacity": node_capacity } for i, _ in enumerate(range(no_nodes))}

def setup_stats_file_writers(nodes: dict[str, int], out_dir: str, marker: str = ""):
    timestamp = int(time.time())
    if len(marker) > 0:
        marker = f"-{marker}"
    return {key: StatsFileWriter(f"{out_dir}/{key}{marker}-{timestamp}.csv") for key in nodes.keys()}

def calc_variance(data: list[float]) -> Tuple[float, float]:
    return np.mean(data), np.std(data)

def plot_with_error_bars(plt, x_labels, data, label: str, marker:str="", **kwargs):
    y, yerr = zip(*data)
    y, yerr = np.array(y), np.array(yerr)
    plt.fill_between(x_labels, alpha=0.15,
                        y1=y - yerr,
                        y2=y + yerr,
                        **kwargs)
    plt.plot(x_labels, y, label=label, marker=marker, **kwargs)

def generate_comparison_plot(plt, x_data, strategies: dict[str, list[Tuple[float, float]]], colors, linestyles: list[str] = None, markers: list[str] = None):
    if linestyles == None:
        # Default behaviour is all all solid.
        linestyles = ['solid'] * len(strategies)
    if markers == None:
        # Default behaviour is all the same.
        markers = ['.'] * len(strategies)
    for idx, (label, data) in enumerate(strategies.items()):
        plot_with_error_bars(plt, x_data, data, label=label, marker=markers[idx], color=colors[idx], linestyle=linestyles[idx])

def aggregate_runs_in_dir(dir):
    aggregated_data = {}
    for data in load_runs_in_dir(dir):
        for key in data:
            if key == "source" or key == "iteration":
                continue
            if key not in aggregated_data:
                aggregated_data[key] = [ [v] for v in data.get(key, []) ]
            else:
                for i, x in enumerate(aggregated_data[key]):
                    x.append(data[key][i])
    return aggregated_data

def load_runs_in_dir(dir):
    """Load and aggregate the runs in a specific directory."""
    with os.scandir(dir) as files:
        plots = [ load_file(f) for f in files
                  if f.path.endswith('.csv') ]
    return plots

def calc_ratio(success, failed) -> float:
    total = success + failed
    if total == 0:
        return 0
    return round(success / (total), 4)

def calc_ratio_over(data, success_key: str, failed_key: str):
    out = []
    for success, failed in zip(data[success_key], data[failed_key]):
        out.append(calc_variance([ calc_ratio(a, b) for a, b in zip(success, failed) ]))
    return out
