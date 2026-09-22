# Changelog

All notable changes to RedScrap are documented in this file.

## [21.9.0] - 2026-09-21

### Added

- Optional binary sentiment analysis using a fitted TF-IDF vectorizer and logistic-regression classifier.
- Sentiment summary table, pie chart and narrative interpretation in the PDF report.
- English and Malay stop-word handling with unigram and bigram frequency analysis.
- Post-type metadata and consistent thread identifiers in Excel exports.
- GUI progress indication, background tasks and cancellation support.

### Improved

- Comment-level Excel export for selected and multiple threads.
- Descriptive, engagement, temporal and yearly summaries.
- Large-table splitting in generated PDF reports.
- Escaping and truncation of user-generated text to reduce ReportLab parsing and layout failures.
- Visibility of zero-comment threads in the full-thread report table.
- Version branding, installation guidance, citation metadata and responsible-use documentation.

### Known limitations

- GUI searches retrieve at most 200 results ordered newest-first; date filtering does not make the search exhaustive.
- Reddit API behaviour, rate limits and content availability can affect retrieval.
- Sentiment output is exploratory and is not validated for every Reddit, Malay-language or research context.

## [1.0.0] - 2025

- Initial stable release of RedScrap for Reddit-based netnographic data collection.
- Basic subreddit, keyword and date filtering.
- Thread and comment retrieval through PRAW.
- Graphical and command-line-compatible components.
- Structured data export and preliminary documentation.
