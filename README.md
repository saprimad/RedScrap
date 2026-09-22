# RedScrap

*A Python tool for Reddit-based netnographic data collection and exploratory analysis*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16756945.svg)](https://doi.org/10.5281/zenodo.16756945)

## Current version

The current GitHub codebase is **RedScrap v2.1.9**. It extends the original RedScrap release with sentiment-analysis support, improved reporting, safer credential handling, enhanced word-frequency analysis, and more robust PDF/Excel export.

The archived Zenodo release remains **v1.0.0** and should be cited using the DOI shown below.

## Key features

- Reddit thread discovery by subreddit, keyword, and date range.
- GUI workflow with a console-compatible fallback for headless environments.
- Export of selected-thread and all-thread comments to Excel.
- Enhanced PDF early report with metadata, descriptive statistics, yearly summaries, engagement summaries, top threads/comments, full thread listings, and visualisations.
- English/Malay-aware word-frequency cleaning with unigram and bigram extraction.
- Optional binary sentiment analysis using a pre-trained TF-IDF vectorizer and classifier.
- Safe local credential storage in `reddit_config.json` rather than hard-coded API credentials.

## Installation

Python 3.9+ is recommended.

```bash
git clone https://github.com/saprimad/RedScrap.git
cd RedScrap
pip install -r requirements.txt
```

On Linux, Tk may need to be installed separately (for example, `python3-tk`).

## Reddit API credentials

Run the program and enter your Reddit API credentials when prompted. RedScrap stores them locally in:

```text
reddit_config.json
```

This file is ignored by Git and should never be committed.

## Optional sentiment model

Sentiment analysis requires two local model files in the same directory as `RedScrap.py`:

```text
sentiment_vectorizer.pkl
sentiment_model.pkl
```

The current implementation is designed for a binary classifier such as a TF-IDF + Logistic Regression model trained on a labelled sentiment dataset. If either model file is missing, RedScrap skips sentiment analysis and continues with the remaining analyses.

## Usage

```bash
python RedScrap.py
```

The GUI allows you to specify the subreddit, keyword(s), start date, and end date, then search, export comments, or generate an early PDF report.

## Important note on sentiment interpretation

The included integration supports binary positive/negative sentiment when compatible local model files are supplied. A model trained on data such as Sentiment140 may not transfer perfectly to Reddit discourse, mixed Malay-English language, sarcasm, or domain-specific discussion. Sentiment results should therefore be treated as exploratory rather than as a substitute for validated stance or qualitative coding.

## Citation

If you use the archived RedScrap release in academic work, please cite:

Tumiran, M. S., Abd Wahab, M. S., Jamal, J. A., & Othman, N. (2025). *RedScrap: Python Tool for Netnographic Data Collection (v1.0.0).* Zenodo. https://doi.org/10.5281/zenodo.16756945

## License

RedScrap is released under the MIT License. See [LICENSE](LICENSE).
