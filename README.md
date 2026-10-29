# RedScrap

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22866437.svg)](https://doi.org/10.5281/zenodo.22866437)

**Current release:** Version 21.9.0  
**Software DOI:** [10.5281/zenodo.22866437](https://doi.org/10.5281/zenodo.22866437)

RedScrap is a Python desktop application for the reproducible collection and preliminary analysis of Reddit discussions for netnographic and other online research. It retrieves threads and comments through the Reddit API using PRAW, exports comment-level data to Excel, and generates an exploratory PDF report.

## Intended users and research contribution

RedScrap is designed to lower the technical barrier to Reddit-based research, particularly for researchers in the social and health sciences who may have limited programming or computational expertise. The graphical desktop interface integrates subreddit and keyword searching, date filtering, thread and comment retrieval, structured Excel export, configurable lexical preprocessing, exploratory reporting and optional sentiment classification without requiring users to build their own API scripts or command-line workflows.

The **Early Report** is intended as an exploratory orientation tool. It provides researchers with a rapid overview of the retrieved dataset before they commit to more intensive qualitative, quantitative or mixed-method analysis. The report summarises broad characteristics such as thread volume, engagement, temporal distribution, lexical patterns and optional exploratory sentiment output. It is not intended to replace formal analytical procedures.


### Comparison with selected Reddit research approaches

| Capability | PRAW | praw-cli | Reddit Data Tool | Communalytic | RedScrap |
|---|---|---|---|---|---|
| Primary interface | Python library | Command line | Browser | Web/no-code | Desktop GUI |
| Programming knowledge required for routine use | Yes | Low–moderate CLI familiarity | No | No | No/minimal |
| Reddit API-based retrieval | Yes | Yes | No (public JSON) | Yes | Yes, via PRAW |
| Subreddit + keyword search | Requires coding | Yes | Limited/single-thread oriented | Yes | Yes |
| Date-based filtering | Requires coding | Yes | Limited | Collection-period/search dependent | Yes |
| Multi-thread comment retrieval | Requires coding | Yes | Limited by browser JSON/thread context | Yes | Yes |
| Structured export | User-defined | JSON/JSONL/CSV/Markdown | CSV/HTML-style export | Platform export | Excel |
| Built-in exploratory lexical summary | No | Filtering only | No | Analysis/visualisation available | Yes |
| Built-in Early Report for dataset orientation | No | No | No | No equivalent RedScrap-style report identified | Yes |
| Optional sentiment output | No | No | No | Platform analysis dependent | Yes, exploratory |
| Researcher-configurable stop-word filtering | Requires coding | CLI/filter configuration | No | Not identified in reviewed collector documentation | Yes |
| Intended low-barrier social/health-science workflow | No | Partial | Partial | Yes | Yes |

This comparison is intended to clarify positioning rather than to claim that RedScrap supersedes other tools. PRAW offers substantially greater programmatic flexibility, praw-cli provides strong command-line extraction and reproducibility features, Reddit Data Tool provides lightweight browser-based thread export, and Communalytic offers a broader no-code computational social-science environment. RedScrap's contribution is its focused local desktop workflow for researchers who want to retrieve Reddit data, inspect an Early Report, and export structured data for subsequent qualitative, quantitative or mixed-method analysis with minimal computing expertise.

## Development background

RedScrap was developed as part of a PhD research project at the Faculty of Pharmacy, Universiti Teknologi MARA (UiTM), Malaysia, to facilitate the systematic collection of Reddit data for netnographic research. The software has since undergone continuous development, with improvements to its data-extraction capabilities, filtering options, user interface, output formats and overall usability. RedScrap is openly archived on Zenodo to promote research transparency, reproducibility, software reuse and formal citation.

## Main features

- Graphical user interface built with Tkinter.
- Search within a specified subreddit using one or more keywords.
- Exact-phrase handling for multi-word keywords and OR-based multi-keyword searches.
- Filtering of returned search results by start and end dates.
- Display of matching threads with a quick summary of thread, comment and upvote counts.
- Export of comments from a selected thread or all returned threads to `.xlsx`.
- Comment-level fields including thread ID, date, post type, thread title, Reddit discussion URL, original source URL, author, comment text and upvotes.
- Exploratory PDF report containing descriptive, engagement, temporal, yearly and lexical summaries, tables and visualisations.
- Configurable lexical preprocessing for word-frequency analysis, with built-in English and Malay stop-word lists plus researcher-supplied custom stop words.
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

## Reddit API credential storage

RedScrap no longer stores the Reddit client secret in plaintext inside `reddit_config.json`. The client ID and user agent may remain in that local configuration file, while the client secret is stored using the operating system credential store through Python `keyring` when available.

Existing installations that still contain a legacy `client_secret` field in `reddit_config.json` are migrated on the next successful launch: RedScrap attempts to save the secret to the operating system credential store and rewrites the local configuration without the secret.

For environments where an operating system credential store is unavailable, credentials may be supplied through the `REDSCRAP_REDDIT_CLIENT_ID`, `REDSCRAP_REDDIT_CLIENT_SECRET`, and `REDSCRAP_REDDIT_USER_AGENT` environment variables. If no secure store or environment secret is available, RedScrap prompts for the secret for the current session rather than persisting it in plaintext.

## Software evaluation

RedScrap includes runtime instrumentation based on Python's `time.perf_counter()` for three user-facing stages: subreddit/keyword searching, Early Report generation and Excel export. The measurements are intended as observed end-to-end runtimes under the stated test conditions rather than hardware-independent performance guarantees.

Functional evaluation was performed using `r/malaysia` with the keyword `langkawi` across three retrieval windows (3 months, 1 year and 2 years). All tested workflows completed successfully. Repeated runs showed consistent report-generation and export times for comparable workloads.

A reproducible first-search latency effect was also observed after a fresh application launch: the first search was substantially slower than subsequent searches, including when tested with another keyword. Because the search stage depends on Reddit/PRAW and network conditions, this behaviour is documented as a fresh-launch first-request/cold-start effect rather than attributed solely to local RedScrap processing.

Full test conditions, raw timings and interpretation are documented in [SOFTWARE_EVALUATION.md](SOFTWARE_EVALUATION.md).

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
4. Optional: select **Lexical Settings** to enable or disable the built-in English and Malay stop-word lists and to add study-specific stop words (comma-separated or one per line).
5. Select **Search Threads**.
6. Choose one of the following actions:
   - **Early Report** to create an exploratory PDF report.
   - **Scrape Selected Thread** to export one thread's comments to Excel.
   - **Scrape All Threads** to export comments from all returned threads to Excel.
6. Select the output filename and location when prompted.

In new Excel exports, **Thread URL** opens the Reddit discussion. **Source URL**
retains the original post destination, such as the linked news article. For a
Reddit self-post the two URLs may point to the same discussion. Existing Excel
files are not changed by this update.

## Search scope and limitations

- The graphical search retrieves a maximum of 200 Reddit search results, ordered newest-first.
- Date filtering is applied only to those returned candidates. A search is therefore reproducible within its stated parameters and retrieval bounds, but it is not an exhaustive historical archive of Reddit.
- When the 200-result retrieval cap is reached, RedScrap now displays a **Search limit reached** warning and reports the number of submissions examined in the GUI summary. The warning informs users that older posts within the selected date range may not have been retrieved and suggests narrowing the keywords or date range.
- Reaching the cap should therefore be treated as a completeness warning rather than evidence that all matching historical posts were retrieved.
- Availability depends on Reddit's API, search behaviour, access rules, rate limits and the continued availability of posts and comments.
- Loading all nested comments can take considerable time for large discussions.
- Deleted, removed or inaccessible content may be missing or represented incompletely.
- The estimated counts displayed in the interface may differ from the final exported number of accessible comments.

## Lexical filtering and language scope

RedScrap uses configurable lexical preprocessing for its word-frequency output. Built-in English and Malay stop-word lists are enabled by default because early development and testing in the Malaysian context showed that common function words could contribute substantial lexical noise and reduce the interpretability of frequency summaries. Researchers may disable either built-in list and may paste additional study-specific stop words directly through **Lexical Settings**.

These settings affect lexical word-frequency output only and do not alter the raw exported Reddit text. This functionality should be understood as configurable preprocessing rather than full multilingual natural-language processing; RedScrap does not currently perform automatic language identification, stemming or lemmatisation.

## Sentiment-analysis limitation

The supplied sentiment component performs binary positive/negative classification using a fitted TF-IDF vectorizer and logistic-regression model trained on the Sentiment140 Twitter dataset. The model has not been externally validated for Reddit discourse, Malay-language content or the user's specific dataset. Sentiment outputs should therefore be treated as exploratory only and should not be interpreted as validated measures of opinion or stance. RedScrap now places this caution directly in the generated PDF report and keeps the accompanying narrative descriptive rather than inferential.

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
