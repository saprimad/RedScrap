# Changelog

All notable changes to RedScrap are documented here.

## [2.1.9] - 2026-09-22

### Added
- Optional binary sentiment-analysis integration using local `sentiment_vectorizer.pkl` and `sentiment_model.pkl` files.
- Enhanced descriptive statistics for upvotes and comment length.
- Post-type summaries and visualisations.
- Yearly thread/comment summaries.
- English/Malay-aware word-frequency cleaning with unigram and bigram extraction.
- Temporal summaries for peak day and peak hour.
- Engagement summaries, top-thread and top-comment tables, and a complete thread list.
- Headless/console fallback when Tkinter cannot initialise.

### Improved
- More robust PDF report generation with table splitting and safer paragraph rendering.
- Handling of long or malformed Reddit text in ReportLab.
- Local credential workflow using `reddit_config.json`.
- Dependency list and project documentation.

### Security
- Removed Reddit API credentials that had previously been embedded in the public source file.
- Added `reddit_config.json` and local model artefacts to `.gitignore`.

### Notes
- Sentiment analysis is optional. If the model files are absent, the remaining RedScrap analyses continue normally.
- Binary sentiment results are exploratory and may not generalise perfectly from training data such as Sentiment140 to Reddit discourse.
- The Zenodo archive currently available for citation is v1.0.0 (DOI: 10.5281/zenodo.16756945). A v2.1.9 Zenodo version can be created from a GitHub release.
