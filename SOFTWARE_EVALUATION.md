# RedScrap Software Evaluation

## Overview

This document records a functional and runtime evaluation of RedScrap under reproducible, researcher-facing test conditions.

The purpose is to show that the main workflow completes successfully across datasets of different sizes and to document observed end-to-end runtime for search/retrieval, Early Report generation and Excel export. These results are not intended as hardware-independent performance guarantees.

## Evaluation environment

The tests were conducted using the RedScrap desktop GUI on a Lenovo ThinkPad X1 Carbon running Windows 11 with a 12th Gen Intel Core i7-1260P processor, 16 GB memory and NVMe storage. A single RedScrap instance was used, and all runs were performed sequentially against the live Reddit service through PRAW.

The internet connection measured approximately 55.53 Mbps download and 87.34 Mbps upload with 9 ms idle latency during the evaluation period. These network measurements are provided only as contextual information and should not be interpreted as a controlled networking benchmark.

Because Reddit retrieval depends on an external API and network conditions, search timings should be interpreted as end-to-end observed latency rather than pure local CPU-processing time. Report-generation and Excel-export timings reflect local processing more directly, although they remain specific to the stated hardware and software environment.

## Runtime instrumentation

RedScrap uses Python's `time.perf_counter()` to record elapsed runtime for three user-facing stages:

1. search/retrieval;
2. Early Report generation; and
3. Excel export.

The timing implementation is contained directly in `RedScrap.py`.

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

| Window | Test | Matching threads | Comments exported | Submissions examined | Search time (s) | Early Report time (s) | Excel export time (s) | Outcome |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 2 years | 0 | 200 | 3,136 | 200 | 84.41 | 92.37 | 0.67 | PASS |
| 2 years | 1 | 200 | 3,137 | 200 | 10.23 | 93.47 | 0.65 | PASS |
| 2 years | 2 | 200 | 3,138 | 200 | 7.27 | 96.54 | 0.65 | PASS |
| 1 year | 3 | 111 | 1,988 | 200 | 4.51 | 66.72 | 0.50 | PASS |
| 1 year | 4 | 111 | 1,989 | 200 | 4.86 | 55.10 | 0.52 | PASS |
| 3 months | 5 | 23 | 212 | 200 | 4.55 | 9.57 | 0.25 | PASS |
| 3 months | 6 | 23 | 213 | 100 | 4.02 | 9.44 | 0.26 | PASS |

*Note: Test 0 represents the cold-start run after fully closing and reopening RedScrap. Tests 1–6 represent subsequent runs under the same general testing environment.*

## Key findings

- Every documented run completed the full workflow successfully.
- Early Report generation increased with workload size, as expected.
- Excel export remained short across the tested datasets.
- Repeated runs of comparable workloads produced similar report-generation and export times.
- Search runtime was more variable because it includes external Reddit/PRAW and network latency.
- Minor changes in exported comment counts between repeated runs are expected because Reddit is a live data source.

## Fresh-launch first-search latency

A pronounced first-search latency was observed after RedScrap had been fully closed and relaunched.

For the 2-year scenario, the first search required 84.41 seconds, while subsequent searches of the same window required 10.23 and 7.27 seconds. The researcher also repeated the fresh-launch comparison using another keyword and observed the same qualitative pattern: the first search after a fresh launch was slower than the second search.

This behaviour is therefore documented as a reproducible fresh-launch first-request/cold-start effect at the application-workflow level. However, the current timing covers the entire end-to-end search stage, which includes Reddit/PRAW and network activity. The observed initial delay should not be interpreted as proof that the latency originates exclusively within RedScrap or exclusively within the Reddit API.

## Dynamic-source note

Reddit is a live data source. Minor differences in comment counts between repeated runs are expected when new comments are added or content availability changes between retrievals. For example, repeated 2-year runs exported 3,136, 3,137 and 3,138 comments while returning the same 200 matching threads.

## Search-result cap

The configured search limit is 200 submissions. A result of 200 matching threads/submissions should not be interpreted as exhaustive historical retrieval.

RedScrap provides an explicit warning when the configured cap is reached before the requested start-date boundary is reached.

## Reproducibility and audit trail

The runtime implementation is available in `RedScrap.py`. This file records the test configuration and observed results used for the evaluation.

Terminal logs and screenshots from the original runs may be retained separately as supplementary audit evidence when required.

**Evaluation status: PASS**
