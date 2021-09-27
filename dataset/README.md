# Dataset

This folder contains the required resources to collect a similar dataset as used in the thesis work.

---

`run.py`

This script is invoked with a file that contains a list of websites to analyse and a `--max-depth` to define how deep we can follow outgoing links.

---

`extract.py`

Expects an `./out/` folder that contains the `content-found.txt` to download to `./out/content/` (by default).  It produces `./out/content-unavailable.txt` which lists the items that could not be found.

---

`clean_page_map.py`

A simple script that removes any entries in `./out/content-unavailable.txt` from `./out/page-map.csv`.

---

`dataset_analyser.py`

Produces two CSV files that can be used to visualise some characteristics of the dataset, like distribution of file sizes and types.
