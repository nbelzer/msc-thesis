from bs4 import BeautifulSoup
from urllib.parse import urlparse
import aiohttp
import asyncio
import argparse
import pathlib

from utils import fetch, gather_with_concurrency

def url_in_blacklist(url):
    return url.endswith('.apk') or url.endswith('.exe')

def clean_url(url, base_url, current_url):
    """Naive function to clean different urls."""
    if url.endswith(":"):
        url = url.rstrip(":")
    if url.startswith('#') or url.startswith('tel:') or url.startswith('mailto:') or url.startswith('data:'):
        return current_url
    if url.startswith('http'):
        return url
    if url.startswith('//'):
        return f"http:{url}"
    if url.startswith('/'):
        return f"{base_url}{url}"
    if url.startswith('javascript:'):
        return current_url
    return f"{current_url}/{url}"

def extract_content(soup):
    """Extract resources based on resource tags from a page."""
    images = [ image.get('src') for image in soup.find_all('img') ]
    stylesheets = [ sheet.get('href') for sheet in soup.find_all('link') ]
    scripts = [ script.get('src') for script in soup.find_all('script') ]
    videos = [ video.get('src') for video in soup.find_all('video') ]
    audio = [ audio.get('src') for audio in soup.find_all('audio') ]
    return [ link for link in images + stylesheets + scripts + videos + audio
             if link and len(link) > 0 ]

def extract_links(soup):
    """Extract outgoing links from a page."""
    a_tags = soup.findAll('a', href=True)
    links = [ link.get('href') for link in a_tags ]
    return [ link for link in links if link and len(link) > 0 ]


async def fetch_page(session, url):
    try:
        return await fetch(session, url)
    except Exception as e:
        return ""

def find_base_url(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


known_pages = {}

async def parse_site(session, url):
    if url in known_pages:
        # If we have seen this page before, return the cached object.
        return known_pages[url]

    print(url)
    soup = BeautifulSoup(await fetch_page(session, url), 'html.parser')
    base_url = find_base_url(url)

    links = [ clean_url(link, base_url, url).lower() for link in extract_links(soup) ]
    content = [ url.lower() ] + [ clean_url(link, base_url, url).lower() for link in extract_content(soup) ]

    known_pages[url] = (links, content)
    return (links, content)

async def parse_site_recursive(session, url, calls=0, max_calls=2):
    links, content = await parse_site(session, url)
    result = { url: (links, content) }
    if calls == max_calls:
        # We cannot go deeper, make sure to provide no links.
        return { url: ([], content) }

    tasks = [ parse_site_recursive(session, page, calls + 1, max_calls) for page in links ]
    sub_results = {}
    for f in await gather_with_concurrency(16, *tasks):
        sub_results.update(f)

    # Always override sub_results with our own as we have a lower call value.
    sub_results.update(result)

    return sub_results


async def main(website_list_url, max_depth=2):
    timeout = aiohttp.ClientTimeout(total=60)
    pages = {}
    async with aiohttp.ClientSession(timeout=timeout) as session:
        with open(website_list_url) as websites:
            for w in websites:
                url = w.rstrip('\n')
                pages.update(await parse_site_recursive(session, url, max_calls=max_depth))

    collected_content = set()
    for p in pages:
        collected_content.update(pages[p][1])

    with open("./out/page-map.csv", "w") as page_map:
        page_map.writelines(f"{i};{' '.join(pages[i][0])};{' '.join(pages[i][1])}\n" for i in pages)

    with open("./out/content-found.txt", "w") as content_file:
        content_file.writelines(f"{i}\n" for i in collected_content)


parser = argparse.ArgumentParser(description='Scrape ')
parser.add_argument('websites', type=pathlib.Path,
                    help='the websites to visit')
parser.add_argument('--max-depth', type=int, default=2,
                    help='how deep to recursively follow links')
args = parser.parse_args()

asyncio.run(main(str(args.websites), max_depth=args.max_depth))
