# RedScrap

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22866437.svg)](https://doi.org/10.5281/zenodo.22866437)

**Current release:** Version 21.9.0  
**Software DOI:** [10.5281/zenodo.22866437](https://doi.org/10.5281/zenodo.22866437)

RedScrap is a Python desktop application for the reproducible collection and preliminary analysis of Reddit discussions for netnographic and other online research. It retrieves threads and comments through the Reddit API using PRAW, exports comment-level data to Excel, and generates an exploratory PDF report.

## Development background

RedScrap was developed as part of a PhD research project at the Faculty of Pharmacy, Universiti Teknologi MARA (UiTM), Malaysia, to facilitate the systematic collection of Reddit data for netnographic research. The software has since undergone continuous development, with improvements to its data-extraction capabilities, filtering options, user interface, output formats and overall usability. RedScrap is openly archived on Zenodo to promote research transparency, reproducibility, software reuse and formal citation.

## Main features

- Graphical user interface built with Tkinter.
- Search within a specified subreddit using one or more keywords.
- Exact-phrase handling for multi-word keywords and OR-based multi-keyword searches.
- Filtering of returned search results by start and end dates.
- Display of matching threads with a quick summary of thread, comment and upvote counts.
- Export of comments from a selected thread or all returned threads to `.xlsx`.
- Comment-level fields including thread ID, date, post type, thread title, thread URL, author, comment text and upvotes.
- Exploratory PDF report containing descriptive, engagement, temporal, yearly and lexical summaries, tables and visualisations.
- English- and Malay-aware word-frequency processing with unigram and bigram support.
- Optional binary sentiment classification using a fitted TF-IDF vectorizer and logistic-regression model.
- Background processing, progress indication and task cancellation for longer operations.

## What is new in v21.9.0

- Integrated the trained TF-IDF vectorizer and binary sentiment classifier.
- Added sentiment counts, percentages, visualisation and narrative output to the PDF report.
- Improved English and Malay stop-word handling and adaptive word-frequency cleaning.
- Added bigram support for more meaningful lexical summaries.
- Added post-type classification and consistent thread IDs to Excel exports.
- Improved the full-thread table and highlighted threads with no comments.
- Improved large-table splitting and handling of long or malformed user-generated text in PDF reports.
- Added asynchronous GUI tasks, progress feedback and cancellation support.
- Standardised release branding, documentation and citation metadata for Version 21.9.0.

## Release files

Place these files in the same folder:

```text
RedScrap.py
sentiment_vectorizer.pkl
sentiment_model.pkl
requirements.txt
README.md
CITATION.cff
CHANGELOG.md
LICENSE
```

The two `.pkl` files are required only for sentiment analysis. All other collection, Excel-export and reporting functions remain available if they are absent.

Do not rename the model files. RedScrap looks specifically for `sentiment_vectorizer.pkl` and `sentiment_model.pkl`.

The supplied models were created with scikit-learn 1.7.2. This version is pinned in `requirements.txt` to avoid model-persistence compatibility warnings. Only load model files obtained from the official RedScrap release because Python pickle-based files can execute code during loading.

## System requirements

- Python 3.10 or later; Python 3.11 is recommended.
- Windows, macOS or Linux with Tkinter support.
- A Reddit API client ID and client secret.
- Internet access while retrieving Reddit data.
- Sufficient memory and storage for the selected threads and their comments.

On some Linux distributions, Tkinter must be installed separately, for example:

```bash
sudo apt install python3-tk
```

## Installation

1. Download or clone the release files.
2. Open a terminal in the RedScrap folder.
3. Create and activate a virtual environment.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

4. Install the dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

5. Run RedScrap:

```bash
python RedScrap.py
```

## Reddit API configuration

RedScrap does not provide shared Reddit API credentials. Each user must request access to the Reddit Data API, obtain Reddit's approval, and use their own registered application's `client_id` and `client_secret`. Researchers should follow the [Reddit for Researchers Program](https://support.reddithelp.com/hc/en-us/articles/49381918834964-Reddit-for-Researchers-Program) guidance and select **I'm a researcher** when submitting the API-access request. Users must also comply with Reddit's [Data API guidance](https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki), Developer Terms and Data API Terms.

After approval and credential registration, launch RedScrap. On first launch, the software requests the user's Reddit client ID and client secret. These credentials are saved locally in `reddit_config.json` and reused in later sessions.

The configuration file has this structure:

```json
{
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET",
  "user_agent": "RedScrap v21.9.0"
}
```

Keep the `client_secret` and `reddit_config.json` private. Never share another person's credentials or upload the configuration file to GitHub, Zenodo or any shared repository. Each RedScrap user is responsible for maintaining their own approval and complying with Reddit's applicable conditions.

## Basic use

1. Enter the subreddit name without `r/`.
2. Enter one or more comma-separated keywords.
3. Enter the start and end dates in `YYYY-MM-DD` format.
4. Select **Search Threads**.
5. Choose one of the following actions:
   - **Early Report** to create an exploratory PDF report.
   - **Scrape Selected Thread** to export one thread's comments to Excel.
   - **Scrape All Threads** to export comments from all returned threads to Excel.
6. Select the output filename and location when prompted.

## Search scope and limitations

- The graphical search retrieves a maximum of 200 Reddit search results, ordered newest-first.
- Date filtering is applied only to those returned candidates. A search is therefore reproducible within its stated parameters and retrieval bounds, but it is not an exhaustive historical archive of Reddit.
- Availability depends on Reddit's API, search behaviour, access rules, rate limits and the continued availability of posts and comments.
- Loading all nested comments can take considerable time for large discussions.
- Deleted, removed or inaccessible content may be missing or represented incompletely.
- The estimated counts displayed in the interface may differ from the final exported number of accessible comments.

## Sentiment-analysis limitation

The supplied sentiment component performs binary positive/negative classification using a fitted TF-IDF vectorizer and logistic-regression model trained on Sentiment140. It was not designed as a substitute for manual qualitative coding and has not been established as a validated measure for Reddit discourse, Malay-language content or the user's specific research domain. Treat its output as exploratory and report the model, training data and limitations transparently.

## Ethical and responsible use

Researchers remain responsible for obtaining any required ethics approval or exemption and for complying with Reddit's applicable terms, institutional requirements and local law. Minimise the collection and disclosure of personal information, avoid reproducing usernames or identifiable quotations unnecessarily, store exported data securely, and consider paraphrasing or aggregation when reporting sensitive discussions.

## Citation

### APA

Tumiran, M. S., Abd Wahab, M. S., Jamal, J. A., & Othman, N. (2026). *RedScrap: Python Tool for Netnographic Data Collection* (Version 21.9.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.22866437

### IEEE

M. S. Tumiran, M. S. Abd Wahab, J. A. Jamal, and N. Othman, “RedScrap: Python Tool for Netnographic Data Collection,” ver. 21.9.0, Zenodo, 2026, doi: 10.5281/zenodo.22866437. [Online]. Available: https://doi.org/10.5281/zenodo.22866437

Machine-readable citation metadata are provided in `CITATION.cff`.

## Authors

- Mad Sapri Tumiran
- Mohd Shahezwan Abd Wahab
- Janattul Ain Jamal
- Nursyuhadah Othman

## Acknowledgements

The development of RedScrap was supported by the Faculty of Pharmacy, Universiti Teknologi MARA (UiTM), Malaysia. The associated research acknowledges NMRR ID-26-03583-QPR and the permission of the Director-General of Health Malaysia to publish relevant research outputs.

## Support

For software-related enquiries, contact `saprimad@moh.gov.my`.

## Licence

RedScrap is distributed under the MIT License. See `LICENSE` for the full terms.
