import re
import csv

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
