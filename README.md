# RedScrap: A Python Tool for Netnographic Data Collection from Reddit

**Version:** 1.1.4  
**Author:** Mad Sapri Tumiran  
**License:** MIT  
**Repository:** [GitHub Link](https://github.com/yourusername/RedScrap)  
**DOI:** [10.5281/zenodo.16756945](https://doi.org/10.5281/zenodo.16756945)

---

## Overview

**RedScrap** is a lightweight, open-source Python tool designed to streamline Reddit data collection for **netnographic** and qualitative research. Built with the PRAW (Python Reddit API Wrapper) library, it enables researchers to extract structured data from Reddit threads or entire subreddits, including comments and metadata.

Version **1.1.4** introduces two notable enhancements:
- **Early Report**: Generates a quick CSV/PDF table of matching threads for preliminary scoping.
- **Scrape All Threads & Save**: One-click bulk extraction of all threads returned by a search.

RedScrap is suitable for qualitative analysis workflows such as **thematic analysis, content analysis, and triangulation**.

---

## Features

- Search Reddit threads by subreddit, keyword(s), and date range.
- **Early Report**: Instant summary of matching threads without full scraping.
- **Scrape Selected Thread & Save**: Extract comments from a chosen thread.
- **Scrape All Threads & Save**: Bulk export all threads in one go.
- Output to CSV or JSON, ready for use in Excel, Atlas.ti, NVivo, or Python-based analysis.
- User-friendly **GUI** and **CLI** options.
- Built-in citation footer for reproducibility.

---

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/yourusername/RedScrap.git
cd RedScrap
pip install -r requirements.txt
```

RedScrap requires **Python 3.7+** and Reddit API credentials.

Register your app at: [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)  
Store your **client_id** and **client_secret** in a `.env` file or directly in the script.

---

## Usage

### CLI Example

```python
from redscrap import RedScrap

scraper = RedScrap()
scraper.scrape_post("https://www.reddit.com/r/malaysia/comments/xxxxx/sample_post/")
scraper.export_to_csv("output.csv")
```

Search subreddit by keyword:

```python
scraper.scrape_subreddit("malaysia", keyword="legalization", limit=100)
```

### GUI Example

Run:

```bash
python gui.py
```

Steps:
1. Enter subreddit (e.g., `malaysia`).
2. (Optional) Add up to three comma-separated keywords.
3. (Optional) Set date range.
4. Click **Search Threads** to load results.
5. Use **Early Report** for a quick CSV/PDF of results.
6. Use **Scrape Selected Thread & Save** for a single thread.
7. Use **Scrape All Threads & Save** for all threads in the search.

Output files are saved with timestamps.

![RedScrap GUI](new-gui-screenshot.png)

---

## Changelog (v1.1.4)

### Added
- Early Report: One-click CSV/PDF summary of matching threads.
- Scrape All Threads & Save: Bulk extraction of all matching threads.
- GUI footer with citation DOI and version label.

### Improved
- Robust logging and retry for bulk scrapes.
- Clearer UI messages during long operations.

---

## Citation

If you use RedScrap in your research, please cite:

> Tumiran, M. S., Abd Wahab, M. S., Jamal, J. A., & Othman, N. (2025). *RedScrap: Python Tool for Netnographic Data Collection* (v1.1.4). Zenodo. https://doi.org/10.5281/zenodo.16756945

---

## License

This project is licensed under the MIT License.

---

## Acknowledgements

Developed as part of a doctoral research study at the Faculty of Pharmacy, Universiti Teknologi MARA (UiTM), Malaysia. Supported by the Ministry of Health Malaysia (KKM) through the Hadiah Latihan Persekutuan (HLP) program.
