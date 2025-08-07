# RedScrap: A Python Tool for Netnographic Data Collection from Reddit

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16756945.svg)](https://doi.org/10.5281/zenodo.16756945)

RedScrap is a lightweight and customizable Python tool for collecting Reddit comments and metadata for netnographic and qualitative research. Built using the PRAW (Python Reddit API Wrapper), RedScrap supports keyword filtering, date range selection, and CSV/JSON output formats. It includes both a CLI and a simple GUI to accommodate different user skill levels.

## Features

- Extract Reddit comments and metadata
- Filter by keyword, post type, and date range
- Output data in CSV or JSON
- CLI and GUI support
- Ideal for digital ethnography, discourse studies, and qualitative research

## Installation

```
pip install -r requirements.txt
```

## Usage

```python
from redscrap import RedScrap

scraper = RedScrap()
scraper.scrape_post("https://www.reddit.com/r/malaysia/comments/xxxxx/sample_post/")
scraper.export_to_csv("output.csv")
```

## Citation

If you use RedScrap in your research, please cite the archived version:

Tumiran, M. S., Wahab, M. S. A., Jamal, J. A., & Othman, N. (2025). *RedScrap: A Python Tool for Netnographic Data Collection from Reddit* (Version 1.0.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.16756945
