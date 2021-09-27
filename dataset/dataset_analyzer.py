import argparse
import pathlib
import os
from enum import Enum
from typing import Tuple

from dataclasses import dataclass
from .utils import read_page_map

class FileType(Enum):
    GRAPHICS = 0
    DOCUMENT = 1
    HTML = 2
    ARCHIVE = 3
    AUDIO = 4
    VIDEO = 5
    FONTS = 6
    DATA = 7
    SCRIPTS = 8
    STYLESHEETS = 9
    UNKNOWN = 10

@dataclass
class ResourceInformation:
    identifier: str
    byte_size: int
    extension: str
    file_type: FileType


@dataclass
class SiteInformation:
    page: str
    byte_size: int
    resources: list[ResourceInformation]


TYPE_TO_EXTENSION = {
    FileType.GRAPHICS: [ 'bmp', 'djvu', 'gif', 'icns', 'ico', 'jpeg', 'jpg', 'png', 'psd', 'raw', 'tif', 'tiff', 'ai', 'svg', 'webp' ],
    FileType.DOCUMENT: [ 'doc', 'docx', 'docm', 'epub', 'md', 'mobi', 'ott', 'txt', 'xls', 'xlsm' ],
    FileType.DATA: ['csv', 'json', 'xml', 'yml', 'yaml', 'log' ],
    FileType.HTML: [ 'htm', 'html' ],
    FileType.ARCHIVE: [ '7z', 'deb', 'dmg', 'exe', 'gzip', 'jar', 'bin', 'rar', 'tar', 'tar.gz', 'zip' ],
    FileType.AUDIO: [ 'aac', 'wav', 'flac', 'wma', 'ac3', 'mp3', 'ots' ],
    FileType.VIDEO: [ 'avi', 'flv', 'm4v', 'mov', 'mpeg', 'mpg', 'mpe', 'webm', 'mkv', 'mp4' ],
    FileType.FONTS: [ 'ttf', 'ttc', 'otf', 'woff' ],
    FileType.SCRIPTS: [ 'js' ],
    FileType.STYLESHEETS: [ 'css' ],
}

EXTENSION_TO_TYPE = {
    ext: file_type for file_type in TYPE_TO_EXTENSION
                   for ext in TYPE_TO_EXTENSION[file_type]
}

def file_type_from_identifier(identifier: str) -> Tuple[str, FileType]:
    root, ext = os.path.splitext(identifier)
    ext = ext.lower().removeprefix('.')
    if len(ext) == 0 or ext not in EXTENSION_TO_TYPE:
        return ext, FileType.UNKNOWN
    return ext, EXTENSION_TO_TYPE[ext]


def scan_files_in_dir(directory):
    """Recursive function that returns all the files in the directory and
    any subdirectories.
    """
    collected_files = []
    with os.scandir(directory) as files:
        for f in files:
            if f.is_file():
                collected_files.append(f)
            elif f.is_dir():
                collected_files.extend(scan_files_in_dir(f))
    return collected_files


"""Will evaluate a downloaded dataset, creating a datafile (csv) that
includes each resource, its identifier, type and size.  In addition it
also creates a datafile (csv) for each web page that includes the url,
number of resources, and aggregated size of all the resources
combined."""
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze a dataset of files.')
    parser.add_argument('graph', type=pathlib.Path,
                        help='the graph that stores the required resources per page.')
    parser.add_argument('directory', type=pathlib.Path,
                        help='the folder containing the dataset.')

    args = parser.parse_args()

    resources = {}
    files = scan_files_in_dir(args.directory)
    for f in files:
        # Size of the file in bytes.
        identifier = f.path.removeprefix(str(args.directory)).removeprefix('/')
        ext, file_type = file_type_from_identifier(identifier)
        resources[identifier] = ResourceInformation(identifier=identifier, byte_size=f.stat().st_size, extension=ext, file_type=file_type)

    unknown_extensions = set([ r.extension for r in resources.values()
                               if r.file_type == FileType.UNKNOWN and r.extension != "" ])
    if len(unknown_extensions) > 0:
        print(f"Found several extensions with no type:\n{unknown_extensions}")

    site_resources = {}
    site_graph = read_page_map(args.graph)
    unknown_resources = set()
    for entry in site_graph.values():
        entry_resources = []
        for r in entry.resources:
            r = r.removeprefix('http://').removeprefix('https://').split('?')[0]
            if r in resources:
                entry_resources.append(resources.get(r))
            elif f"{r}index.html" in resources:
                entry_resources.append(resources.get(f"{r}index.html"))
            elif f"{r}/index.html" in resources:
                entry_resources.append(resources.get(f"{r}/index.html"))
            else:
                unknown_resources.add(r)

        total_bytes = sum([ r.byte_size for r in entry_resources ])
        site_resources[entry.page] = SiteInformation(page=entry.page, byte_size=total_bytes, resources=entry_resources)

    print("Writing unavailable resources to ./out/resources-unavailable.txt")
    with open('out/resources-unavailable.txt', 'w') as f:
        for r in unknown_resources:
            f.write(f"{r}\n")

    print("Writing resource stats to ./out/dataset-resource-stats.csv")
    with open('out/dataset-resources-stats.csv', 'w') as f:
        f.write('identifier;size;extension;type\n')
        for r in resources.values():
            f.write(f"{r.identifier.replace(';', '')};{r.byte_size};{r.extension};{r.file_type.name}\n")

    print("Writing page stats to ./out/dataset-pages-stats.txt")
    with open('out/dataset-pages-stats.csv', 'w') as f:
        f.write('page;size;no_resources\n')
        for p in site_resources.values():
            f.write(f"{p.page.replace(';', '')};{p.byte_size};{len(p.resources)}\n")
