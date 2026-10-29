# RedScrap Software Evaluation

## Purpose

This document records the functional and runtime evaluation performed in response to reviewer feedback requesting clearer software test cases and performance evidence.

The evaluation is intended to document observed end-to-end runtime and process success under reproducible test conditions. It is not intended as a hardware-independent benchmark.

## Runtime instrumentation

RedScrap uses Python's `time.perf_counter()` to record elapsed runtime for three stages:

1. search/retrieval;
2. Early Report generation; and
3. Excel export.

These measurements include the user-visible end-to-end duration of each stage. Search runtime therefore includes external Reddit/PRAW/API and network latency as well as local filtering and interface processing.

## Test configuration

Common settings:

- Subreddit: `r/malaysia`
- Keyword: `langkawi`
- English lexical stop words: enabled
- Malay lexical stop words: disabled
- Additional custom stop words: none
- Workflow sequence: Search Threads -> Early Report -> Scrape All Threads

Date windows:

| Scenario | Start date | End date |
|---|---|---|
| 3 months | 2026-07-29 | 2026-10-29 |
| 1 year | 2025-10-29 | 2026-10-29 |
| 2 years | 2024-10-29 | 2026-10-29 |

## Results

| Window | Run | Matching threads | Comments exported | Submissions examined | Search time (s) | Early Report time (s) | Excel export time (s) | Outcome |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 3 months | 1 | 23 | 212 | 200 | 4.55 | 9.57 | 0.25 | PASS |
| 3 months | 2 | 23 | 213 | 100 | 4.02 | 9.44 | 0.26 | PASS |
| 1 year | 1 | 111 | 1,988 | 200 | 4.51 | 66.72 | 0.50 | PASS |
| 1 year | 2 | 111 | 1,989 | 200 | 4.86 | 55.10 | 0.52 | PASS |
| 2 years | 1 | 200 | 3,136 | 200 | 84.41 | 92.37 | 0.67 | PASS |
| 2 years | 2 | 200 | 3,137 | 200 | 10.23 | 93.47 | 0.65 | PASS |
| 2 years | 3 | 200 | 3,138 | 200 | 7.27 | 96.54 | 0.65 | PASS |

## First-search latency after a fresh launch

A pronounced first-search latency was observed after RedScrap had been fully closed and relaunched.

For the 2-year scenario, the first search required 84.41 seconds, while subsequent searches of the same window required 10.23 and 7.27 seconds. The researcher additionally repeated the fresh-launch comparison using another keyword and again observed that the first search was slower than the second search.

This pattern is therefore reproducible at the application-workflow level and is documented as a fresh-launch first-request/cold-start effect. However, RedScrap relies on Reddit/PRAW and the network during search, and the current instrumentation measures the complete end-to-end search stage. The observed initial delay should therefore not be interpreted as proof that the latency originates exclusively within RedScrap itself or exclusively within the Reddit API.

## Functional outcome

All documented runs completed successfully through the full workflow:

- search/retrieval;
- Early Report generation; and
- Excel export.

Report-generation time increased with the number of retrieved threads, while Excel export remained short for the tested datasets. Report and export times were relatively consistent across repeated runs of comparable workloads.

## Dynamic-source note

Reddit is a live data source. Minor differences in comment counts between repeated runs are expected when new comments are added or content availability changes between retrievals. For example, repeated 2-year runs exported 3,136, 3,137 and 3,138 comments while returning the same 200 matching threads.

## Search-result cap

The configured search limit is 200 submissions. A result of 200 matching threads/submissions should not be interpreted as exhaustive historical retrieval. The software provides an explicit warning when the configured cap is reached before the requested start-date boundary is reached.

## Reproducibility and audit trail

The runtime implementation is available in `RedScrap.py`. Terminal logs or screenshots from the evaluation runs can be retained separately as supplementary audit evidence if required.

Evaluation status: **PASS**
