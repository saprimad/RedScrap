
---
title: 'RedScrap: A Python Tool for Netnographic Data Collection from Reddit'
tags:
  - Python
  - Reddit
  - Netnography
  - Qualitative Research
  - Digital Ethnography
authors:
  - name: Mad Sapri Tumiran
    orcid: 0009-0006-2634-5009
    affiliation: 1
  - name: Mohd Shahezwan Abd. Wahab (Dr.)
    orcid: 0000-0002-2801-0134
    affiliation: 1
  - name: Jannatul Ain Jamal (Dr.)
    affiliation: 1
  - name: Nursyuhadah Othman (Dr.)
    affiliation: 1
affiliations:
  - name: Faculty of Pharmacy, Universiti Teknologi MARA, Malaysia
    index: 1
date: 2025-08-06
---

## Summary

Netnography has become an essential approach for understanding online communities and public discourse. Reddit, as a platform centered around interest-based subreddits and largely anonymous user interactions, offers a valuable source of user-generated content for such studies. However, manual data collection from Reddit can be challenging for researchers unfamiliar with API interaction or data extraction methods.

**RedScrap** is a lightweight and customizable Python tool designed to support netnographic research by automating the collection of Reddit comments and metadata. Developed using the PRAW (Python Reddit API Wrapper) library, RedScrap enables researchers to extract structured data from Reddit threads or subreddits, with support for filtering by keyword, post type, and date range. The tool outputs data in standard formats (CSV, JSON), making it suitable for qualitative coding, thematic analysis, and digital discourse studies.

## Statement of Need

Researchers in the fields of digital ethnography, communication, and social sciences often require access to structured Reddit data for qualitative analysis. However, most existing solutions are either technically complex or not tailored for academic workflows. RedScrap addresses this gap by providing an accessible, open-source solution to efficiently collect and export Reddit data for research purposes.

## Installation

To install the required dependencies:

```
pip install -r requirements.txt
```

## Usage

RedScrap can be used in Python scripts or Jupyter notebooks to extract Reddit comments and metadata for qualitative analysis. Users can target a specific Reddit post, an entire subreddit, or filter comments by keyword or date range. For example:

```python
from redscrap import RedScrap

scraper = RedScrap()
scraper.scrape_post("https://www.reddit.com/r/malaysia/comments/xxxxx/sample_post/")
scraper.export_to_csv("output.csv")
```

In addition to the command-line interface, RedScrap also includes a simple graphical user interface (GUI) that allows users to extract Reddit comments without writing code. Users can input a target subreddit (e.g., `malaysia`), enter a keyword, and define a date range. After clicking **Search Threads**, the tool will display matching threads. The user can then select a thread and click **Scrape Selected Thread & Save** to export the comments and metadata into a structured file (CSV or JSON) for further analysis.

## Acknowledgements

RedScrap was developed as part of a PhD research project at Universiti Teknologi MARA, supported by the Ministry of Health Malaysia. It is designed to support netnographic research using Reddit data and aims to help researchers efficiently collect and analyze public discourse from digital communities.

Refference  
Cherecheș, M., Finta, H., Prisada, R., & Rusu, A. (2024). Pharmacists’ Professional Satisfaction and Challenges: A Netnographic Analysis of Reddit and Facebook Discussions. Pharmacy, 12, 1-33. https://doi.org/10.3390/pharmacy12050155  
Chi, Y., & Chen, H. Y. (2023). Investigating Substance Use via Reddit: Systematic Scoping Review [Review]. Journal of Medical Internet Research, 25, Article e48905. https://doi.org/10.2196/48905  
Jeacle, I. (2020). Navigating netnography: A guide for the accounting researcher. Financial Accountability & Management. https://doi.org/10.1111/faam.12237  
Kozinets, R. V., & Gretzel, U. (2024). Netnography evolved: New contexts, scope, procedures and sensibilities. Annals of Tourism Research, 104, 103693. https://doi.org/10.1016/j.annals.2023.103693  
Rocha-Silva, T., Nogueira, C., & Rodrigues, L. (2024). Passive data collection on Reddit: a practical approach. Research Ethics, 20(3), 453-470. https://doi.org/10.1177/17470161231210542  
Strand, M. (2022). Attitudes towards disordered eating in the rock climbing community: a digital ethnography [Article]. Journal of Eating Disorders, 10(1), Article 96. https://doi.org/10.1186/s40337-022-00619-5  
