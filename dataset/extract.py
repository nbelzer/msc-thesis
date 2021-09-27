from urllib.parse import urlparse
import os
from utils import fetch_bytes, gather_with_concurrency
import asyncio
import aiohttp
import argparse
import pathlib

async def fetch_content(session, url, output_location="out/content/"):
    parsed = urlparse(url)
    domain = parsed.netloc
    path = parsed.path

    if ".." in path:
        # Ignore all relative path elements.
        return url
    if "." not in path and len(path) > 0:
        path = os.path.join(path, "index.html")
    if path.endswith('/') or len(path) == 0:
        path = os.path.join(path, "index.html")

    file_path = os.path.join(output_location, domain, path.lstrip('/'))

    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            c = await fetch_bytes(session, url)
            if len(c) > 0:
                f.write(c)
            else:
                raise Exception("Empty file")
        return None
    except Exception as e:
        print(f"[E] Unable to store {file_path} from {url}:\n{e}")
        return url

async def main(output_location="out/content/"):
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        with open("./out/content-found.txt", "r") as content:
            tasks = [ fetch_content(session, c.rstrip('\n'), output_location) for c in content ]
            failed_downloads = await gather_with_concurrency(256, *tasks)
        print(f"Downloaded all files to {output_location}")
        with open('./out/content-unavailable.txt', 'a') as f:
            for failed_item in failed_downloads:
                if failed_item != None:
                    f.write(f"{failed_item}\n")
        print(f"Written failed downloads to ./out/content-unavailable.txt")


parser = argparse.ArgumentParser(description='Content extractor, downloads scraped files.')
parser.add_argument('content_location', type=pathlib.Path,
                    help='what folder to download the content to', default='./out/content/')
args = parser.parse_args()

asyncio.run(main(args.content_location))
