# RedScrap Software Evaluation

## Overview

This document records a functional and runtime evaluation of RedScrap under reproducible, researcher-facing test conditions.

The purpose is to show that the main workflow completes successfully across datasets of different sizes and to document observed end-to-end runtime for search/retrieval, Early Report generation and Excel export. These results are not intended as hardware-independent performance guarantees.

## Evaluation environment

The tests were conducted using the RedScrap desktop GUI on a Lenovo ThinkPad X1 Carbon running Windows 11 with a 12th Gen Intel Core i7-1260P processor, 16 GB memory and NVMe storage. A single RedScrap instance was used, and all runs were performed sequentially against the live Reddit service through PRAW.

The internet connection measured approximately 55.53 Mbps download and 87.34 Mbps upload with 9 ms idle latency during the evaluation period. These network measurements are provided only as contextual information and should not be interpreted as a controlled networking benchmark.

Because Reddit retrieval depends on an external API and network conditions, search timings should be interpreted as end-to-end observed latency rather than pure local CPU-processing time. Early Report generation can include comment retrieval as well as local processing. In the report-before-export sequence, subsequent Excel export may reuse cached PRAW comment objects. These stage timings are specific to the workflow and environment; they do not isolate cold-start comment acquisition.

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

The general-use search limit is 200 submissions, retained as an operational safeguard to bound workload and API usage. It is an application-level setting, not an inherent software capacity limit or a Reddit blocking threshold, and does not guarantee avoidance of rate limiting. A result of 200 matching threads/submissions should not be interpreted as exhaustive historical retrieval. The separate experiment below removes this cap on the experimental branch only.

RedScrap provides an explicit warning when the configured cap is reached before the requested start-date boundary is reached.

## Retrieval without the 200-thread limit

### Scope and evidence

Two successive live runs on 31 October 2026 used the experimental branch `test/no-thread-cap`, subreddit `r/malaysia`, keyword `langkawi`, newest-first sorting and the date window 29 October 2024–29 October 2026 (UTC, inclusive end date). The researcher selected the option to remove the application-level 200-submission cap (`limit=None`). The first run used the earlier GUI label **No user-defined limit**; the second screenshot shows **Remove 200-thread limit**. The actual local commit SHA and hardware configuration were not included in these supplied run logs; the environment description above concerns the original evaluation.

The two supplied JSON search logs, Excel exports and PDF reports were inspected, and all exported Excel values were compared row by row. Search times and status come from JSON; report and export runtimes come from the supplied console output. Raw datasets and screenshots are retained separately by the researcher and are not published in this repository update.

### Observed results

| Measure | Run 1 | Run 2 |
|---|---:|---:|
| Submissions examined | 242 | 242 |
| Matching threads (JSON and PDF) | 242 | 242 |
| Duplicate submissions detected by search | 0 | 0 |
| Exported comment rows | 3,434 | 3,434 |
| Distinct thread URLs represented in Excel | 209 | 209 |
| Search time (s) | 6.407 | 7.547 |
| Early Report generation time (s) | 123.42 | 120.56 |
| Subsequent Excel export time (s) | 0.81 | 0.70 |

Both searches ended with `available_results_exhausted`. This means that the available API search iterator ended, not that all historical matching Reddit posts were retrieved.

### Export consistency and text screening

The exports have the same nine columns and 3,434 rows. Every row matches in order across Thread ID, Date, Post Type, Thread Title, Thread URL, Source URL, Author and Comment. Only Upvotes differs, on 898 rows. No duplicate complete rows were found in either export. Individual Reddit comment IDs are not exported, so this finding establishes equality of exported fields rather than identity verified by comment IDs.

Each export contains 47 `[removed]` markers, 31 `[deleted]` markers and one empty text record. Screening ignores surrounding whitespace and a leading Excel-protection apostrophe. Excluding these 79 records leaves **3,355 rows containing text**, before relevance assessment or further cleaning. The supplied raw files were not modified.

The 242 search results are distinct from the 209 thread URLs represented by comment rows. The remaining 33 threads have no rows in the comment export; the supplied files do not establish the individual reasons. The GUI estimate of approximately 3,700 comments must also be distinguished from the 3,434 records actually exported.

Both PDFs report the same comment-length descriptive statistics, post-type counts and binary sentiment counts (1,829 positive; 1,605 negative). Total reported comment scores differ: 22,949 versus 22,943. Sentiment counts are exploratory classifier outputs, not human-validated sentiment labels.

### Interpretation and limitations

The run demonstrates retrieval beyond the configured 200-submission cap and consistency of exported text and record order across two successive runs of this query. It does not establish maximum capacity, unlimited API access, complete historical coverage or general repeatability across other datasets.

Execution order was **Search Threads → Early Report → Scrape All Threads**. The report can retrieve comments before export, so the later 0.81 s and 0.70 s exports may use cached comment objects. They are not cold-start end-to-end comment retrieval benchmarks.

The previously documented capped T1 returned 200 threads and 3,137 raw comments. These experimental runs returned 42 more threads and 297 more raw comment records. Because the earlier and current collections occurred at different times, these differences cannot all be attributed to the cap alone. A contemporaneous capped control and underlying record comparison would be needed for that attribution; cleaning criteria must also be aligned before comparing screened counts.

### Branch policy and run record

The 200-submission safeguard remains the default for general use. Keep this experiment on `test/no-thread-cap`; **do not merge the experimental code into `main`**. See [RETRIEVAL_WITHOUT_200_THREAD_LIMIT.md](RETRIEVAL_WITHOUT_200_THREAD_LIMIT.md) for run instructions, timestamps and evidence filenames.

## Reproducibility and audit trail

The runtime implementation is available in `RedScrap.py`. This file records the test configuration and observed results used for the evaluation.

Terminal logs and screenshots from the original runs may be retained separately as supplementary audit evidence when required.

**Evaluation status: PASS**
