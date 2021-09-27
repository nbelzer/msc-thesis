from collections import defaultdict
import numpy as np
from statistics import mean
import csv

def __average_data_over_window(data, window=5):
    return [data[0]] + [mean(data[max(0, i - window) :i]) for i in range(len(data)) if i > 0]

def __total_to_delta(a: list[int]) -> list[int]:
    total = 0
    delta = []
    for v in a:
        delta.append(v - total)
        total = v
    return delta

def aggregate_data_for_files(files):
    plots = []
    for f in files:
        plots.append(load_file(f))

    aggregated_data = {}
    for data in plots:
    #    create_plots(data, title=data["source"])
        for key in data:
            if key == "source" or key == "iteration":
                continue
            if key not in aggregated_data:
                aggregated_data[key] = data.get(key, [])
            else:
                aggregated_data[key] = np.sum(np.array([data[key], aggregated_data.get(key, [])]), axis=0)
    return aggregated_data, plots

def load_file(f):
    data = defaultdict(list)
    with open(f, 'r') as f:
        stats_reader = csv.DictReader(f, delimiter=';')
        for row in stats_reader:
            for key, value in row.items():
                # Parse each value as an int as there are no floats in our current data files.  As this changes this line also needs to change to something more complex.
                data[key].append(int(value))
    data = {
        'iteration': data['iteration'],
        'hits_total': data['hits'],
        'misses_total': data['misses'],
        'cache_bytes_total': data['cache_bytes'],
        'origin_bytes_total': data['origin_bytes'],
        'neighbour_bytes_total': data['neighbour_bytes'],
        'items_total': data['no_items'],
        'cache_total': data['bytes_used'],
        'requests_to_origin': data['requests_to_origin'],
        'requests_to_neighbours': data['requests_to_neighbours'],
        'requests_to_neighbours_success': data['requests_to_neighbours_success']
    }
    data.update({
        'source': f,
        'hits': __total_to_delta(data['hits_total']),
        'misses': __total_to_delta(data['misses_total']),
        'cache_bytes_added': __total_to_delta(data['cache_bytes_total']),
        'origin_bytes_added': __total_to_delta(data['origin_bytes_total']),
        'neighbour_bytes_added': __total_to_delta(data['neighbour_bytes_total']),
        'items_added': __total_to_delta(data['items_total']),
        'cache_added': __total_to_delta(data['cache_total']),
        'requests_to_origin_added': __total_to_delta(data['requests_to_origin']),
        'requests_to_neighbours_added': __total_to_delta(data['requests_to_neighbours']),
        'requests_to_neighbours_success_added': __total_to_delta(data['requests_to_neighbours_success']),
    })
    return data


def extract_value_error(data):
    tuples = [ [ float(x) for x in v.split('+')] for v in data ]
    values, error = zip(*tuples)
    return np.array(values), np.array(error)
