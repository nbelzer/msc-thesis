import asyncio
from dataclasses import dataclass

@dataclass
class PageMapEntry:
    page: str
    resources: list[str]
    outgoing_links: list[str]


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


async def fetch_bytes(session, url):
    async with session.get(url) as response:
        return await response.read()


async def gather_with_concurrency(n, *tasks):
    """
    Execute tasks concurrently with a max amount of tasks running at the same time.
    Retrieved from https://stackoverflow.com/a/61478547/7868972.
    """
    semaphore = asyncio.Semaphore(n)

    async def sem_task(task):
        async with semaphore:
            return await task
    return await asyncio.gather(*(sem_task(task) for task in tasks))


def read_page_map(path) -> dict[str, PageMapEntry]:
    """Read a page map from file."""
    page_map = {}
    with open(path, 'r') as content_map:
        for line in content_map:
            parsed = line.split("\n")[0].split(';')
            if len(parsed) != 3:
                continue
            origin = parsed[0]
            links = parsed[1].split(' ')
            resources = parsed[2].split(' ')
            page_map[origin] = PageMapEntry(page=origin, outgoing_links=links, resources=resources)

    return page_map
