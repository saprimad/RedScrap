---
title: "RedScrap: A Python Tool for Netnographic Data Collection from Reddit"
tags:
  - Python
  - Reddit
  - Netnography
  - Qualitative Research
  - Digital Ethnography
authors:
  - name: "Mad Sapri Tumiran"
    orcid: 0009-0006-2634-5009
    affiliation: 1
  - name: "Mohd Shahezwan Abd Wahab"
    orcid: 0000-0002-2801-0134
    affiliation: 1
  - name: "Janattul Ain Jamal"
    orcid: 0009-0009-7083-7512
    affiliation: 1
  - name: "Nursyuhadah Othman"
    orcid: 0000-0002-0650-3456
    affiliation: 1
affiliations:
  - name: "Faculty of Pharmacy, Universiti Teknologi MARA, Malaysia"
    index: 1
date: 2026-09-21
---

## Summary

Netnography examines online communities and naturally occurring digital interactions. Reddit offers extensive topic-based discussions, but systematic collection can be technically difficult for researchers who are unfamiliar with APIs or programming.

RedScrap is an open-source Python desktop application for collecting and organising Reddit threads and comments for netnographic and related online research. It uses PRAW to search a specified subreddit by keyword and date parameters, exports comment-level data to Excel, and produces an exploratory PDF report. Version 21.9.0 adds improved descriptive, engagement, temporal, yearly and lexical summaries, English/Malay-aware term processing, robust report generation, and optional binary sentiment classification.

## Statement of Need

Many available Reddit tools prioritise large-scale computational workflows. Qualitative researchers often need a more accessible process for identifying relevant discussions, reviewing thread metadata and exporting comment-level material for later screening or coding. RedScrap provides a graphical workflow while retaining reusable Python classes for retrieval, analysis and export.

The exported Excel data include thread ID, date, post type, thread title, thread URL, author, comment text and upvotes. The PDF report supports preliminary scoping and descriptive exploration; it is not a substitute for formal qualitative analysis or validated stance coding.

## Implementation and Functionality

RedScrap provides:

- subreddit and keyword-based thread discovery through PRAW;
- start- and end-date filtering of returned search candidates;
- selected-thread and multi-thread comment export to Excel;
- descriptive, engagement, temporal and yearly summaries;
- English/Malay-aware unigram and bigram frequency analysis;
- tables and visualisations in an exploratory PDF report;
- optional positive/negative sentiment classification using a fitted TF-IDF vectorizer and logistic-regression model; and
- background GUI tasks, progress feedback and cancellation support.

The graphical search retrieves a maximum of 200 results ordered newest-first. Date filtering is applied to those returned candidates, so a search is reproducible within its stated parameters and retrieval bounds but is not an exhaustive historical archive of Reddit.

## Installation

RedScrap requires Python 3.10 or later; Python 3.11 is recommended.

```bash
git clone https://github.com/saprimad/RedScrap.git
cd RedScrap
python -m venv .venv
python -m pip install -r requirements.txt
python RedScrap.py
```

Users must request access to the Reddit Data API, obtain Reddit's approval, and use their own registered application's `client_id` and `client_secret`. Researchers should follow the Reddit for Researchers guidance and select **I'm a researcher** when applying. RedScrap does not provide shared credentials. Credentials are stored locally in `reddit_config.json`, which must remain private and is excluded from version control.

## Usage

In the graphical interface:

- enter a subreddit name without `r/`;
- enter one or more comma-separated keywords;
- provide a start and end date in `YYYY-MM-DD` format;
- select **Search Threads**;
- generate an **Early Report**, export a selected thread, or export all returned threads; and
- choose the output filename and location when prompted.

The optional sentiment component requires `sentiment_vectorizer.pkl` and `sentiment_model.pkl` in the same directory as `RedScrap.py`. If either file is unavailable, the remaining collection, Excel-export and reporting functions continue to operate.

## Limitations and Ethical Use

Reddit API behaviour, rate limits, content deletion and access restrictions can affect retrieval. Loading nested comments may take considerable time for large discussions. The supplied sentiment model was trained using Sentiment140 and has not been established as a validated measure for Reddit discourse, Malay-language content or a user's specific research domain. Its output should be treated as exploratory.

Researchers remain responsible for obtaining any required ethics approval or exemption, complying with Reddit's applicable terms and local law, minimising collection and disclosure of personal information, and storing exported data securely.

## Development Background

RedScrap was developed as part of a PhD research project at the Faculty of Pharmacy, Universiti Teknologi MARA (UiTM), Malaysia, to facilitate the systematic collection of Reddit data for netnographic research. The software has since undergone continuous development, with improvements to its data-extraction capabilities, filtering options, user interface, output formats and overall usability. RedScrap is openly archived on Zenodo to promote research transparency, reproducibility, software reuse and formal citation.

## Software Availability

- Source code: https://github.com/saprimad/RedScrap
- Archived release: https://doi.org/10.5281/zenodo.22866437
- Version: 21.9.0
- Licence: MIT

## Acknowledgements

The development of RedScrap was supported by the Faculty of Pharmacy, Universiti Teknologi MARA (UiTM), Malaysia. The associated research acknowledges NMRR ID-26-03583-QPR and the permission of the Director-General of Health Malaysia to publish relevant research outputs.

## Citation

Tumiran, M. S., Abd Wahab, M. S., Jamal, J. A., & Othman, N. (2026). *RedScrap: Python Tool for Netnographic Data Collection* (Version 21.9.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.22866437

## References

Cherecheș, M., Finta, H., Prisada, R., & Rusu, A. (2024). Pharmacists’ professional satisfaction and challenges: A netnographic analysis of Reddit and Facebook discussions. *Pharmacy*, 12, 1–33. https://doi.org/10.3390/pharmacy12050155

Chi, Y., & Chen, H. Y. (2023). Investigating substance use via Reddit: Systematic scoping review. *Journal of Medical Internet Research*, 25, e48905. https://doi.org/10.2196/48905

Jeacle, I. (2020). Navigating netnography: A guide for the accounting researcher. *Financial Accountability & Management*. https://doi.org/10.1111/faam.12237

Kozinets, R. V., & Gretzel, U. (2024). Netnography evolved: New contexts, scope, procedures and sensibilities. *Annals of Tourism Research*, 104, 103693. https://doi.org/10.1016/j.annals.2023.103693

Rocha-Silva, T., Nogueira, C., & Rodrigues, L. (2024). Passive data collection on Reddit: A practical approach. *Research Ethics*, 20(3), 453–470. https://doi.org/10.1177/17470161231210542

Strand, M. (2022). Attitudes towards disordered eating in the rock climbing community: A digital ethnography. *Journal of Eating Disorders*, 10(1), 96. https://doi.org/10.1186/s40337-022-00619-5

