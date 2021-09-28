from dataclasses import dataclass
from typing import Optional
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

@dataclass
class Page:
    """Represents a web page."""
    url: str
    outgoing_links: set[str]
    resources: set[str]

def read_page_map(path) -> dict[str, Page]:
    CLEAN_URL_REGEX = re.compile("^https?://([^?]*)", re.IGNORECASE)
    def clean_url(url: str) -> Optional[str]:
        """Removes the prefix 'https?://' and any parameters from the url.

        Also filters out any url that doesn't conform to the regex by
        returning `None`.
        """
        match = CLEAN_URL_REGEX.match(url)
        if match == None:
            return None
        return match.group(1)

    def clean_urls(urls: list[str]) -> list[str]:
        return list(filter(lambda x: x != None and len(x) > 0, map(clean_url, urls)))

    """Read a page map from file."""
    page_map = {}
    with open(path, 'r') as content_map:
        for line in content_map:
            parsed = line.split("\n")[0].split(';')
            if len(parsed) != 3:
                continue
            origin = clean_url(parsed[0])
            if origin == None:
                continue
            links = set(clean_urls([ x for x in parsed[1].split(' ') if len(x) > 0 ]))
            resources = set(clean_urls([ x for x in parsed[2].split(' ') if len(x) > 0 ]))
            page_map[origin] = Page(url=origin, outgoing_links=links, resources=resources)

    return page_map
