# Retrieval Without the 200-Thread Limit

Branch: `test/no-thread-cap`. This branch is for a comparison run; it is not merged into main.

## Run on Windows

From an existing RedScrap checkout, with its normal dependencies and Reddit credentials:

```powershell
git fetch origin
git switch --track origin/test/no-thread-cap
python RedScrap.py
```

If the local branch already exists, use `git switch test/no-thread-cap` instead. Commit or stash local edits before switching if Git reports a conflict.

1. Use subreddit `malaysia`, keyword `langkawi`, start `2024-10-29`, end `2026-10-29` (UTC, inclusive end date).
2. Tick **Remove 200-thread limit**, then **Search Threads**. Unticked retains the previous 200-submission cap.
3. Wait for the search status or use **Cancel**. Cancellation is cooperative between submissions; an active network request or PRAW rate-limit wait must finish first.
4. Choose **Save Search Log** to export the settings, timestamps, elapsed time, examined count, matching unique threads and termination status as JSON. It excludes credentials. PRAW retry counts are not instrumented; the log explicitly says so.
5. For a normal finished run, use **Scrape All Threads** and **Early Report**. Save outputs with a distinct `T7_NoCap` name; do not overwrite T1. Search-log counts are thread counts; the displayed comment totals are Reddit metadata estimates until comments are actually exported.
6. Retain the JSON, XLSX, PDF, branch commit and test date together. A fresh 200-cap control run on the same day is useful because search results can change since T1.

## Interpret the status

- `available_results_exhausted`: the available API search iterator ended. This does not prove all historical matching Reddit posts were retrieved.
- `user_cap_reached`: the configured submission cap was reached. The cap counts examined submissions before local date filtering.
- `cancelled`: user stopped the run; retained results are partial.
- `api_or_error_interruption`: a request or processing error interrupted the run; retained results are partial.

No API restrictions are bypassed. `limit=None` removes only RedScrap's user-defined cap; Reddit search availability and PRAW behaviour still apply. Do not describe this as unlimited Reddit access or as proof of complete coverage. Do not assume uncapped retrieval must exceed 200 results.

## Offline validation

```powershell
python -m unittest discover -s tests -v
python -m py_compile RedScrap.py
```

Tests execute the real Scraper and GUI search methods with fake Reddit responses. They cover 350 returned submissions, the existing cap, duplicate IDs, date boundaries, cancellation, empty results, API interruption, cap validation and GUI forwarding/control restoration. They require no credentials or live Reddit requests. Full desktop visual QA and the live T7 collection must be performed on the researcher's configured machine.

## Recorded live run — 31 October 2026

The researcher ran the experimental branch on their configured Windows machine and supplied the console output below as the source for these results. The exported JSON, XLSX and PDF have not been independently inspected for this entry.

| Setting or result | Recorded value |
| --- | --- |
| Tested code commit | `b3f186728d93cdde996c28ca25692e6177e156a3` (branch implementation provided for this run; local checkout SHA not included in the supplied console log) |
| Subreddit | `malaysia` |
| Keyword / query | `langkawi` |
| Requested date range | 29 October 2024–29 October 2026, UTC, inclusive end date |
| Search order | `new` |
| User-defined thread cap | None (`limit=None`) |
| Search start (UTC) | 2026-10-31T02:06:37.932999+00:00 |
| Search end (UTC) | 2026-10-31T02:06:44.331952+00:00 |
| Search elapsed time (reported timer) | 6.407 seconds |
| Submissions examined | 242 |
| Matching threads | 242 |
| Duplicate submissions detected | 0 |
| Search termination status | `available_results_exhausted` |
| Early Report generation time | 123.42 seconds |
| Subsequent all-thread comment export time | 0.81 seconds |
| Comments exported | 3,434 |
| Execution order | Search → Early Report → Scrape All Threads |
| Sentiment analysis | Console reported successful loading of the trained TF-IDF vectorizer and classifier |
| Retry count | Not instrumented; handled by PRAW |

### Interpretation and timing limits

This live run demonstrates retrieval beyond the researcher-configured 200-submission cap. The 200 setting is a conservative operational safeguard for general use, intended to bound workload and API usage; it is not an inherent RedScrap capacity limit or a Reddit blocking threshold. It does not itself guarantee avoidance of rate limiting.

The search iterator exhausted the results available for this query through the API. This is not evidence of complete historical Reddit coverage. The 3,434 figure is the console-reported exported comment count, not an independently verified cleaned or analysable comment count.

The report ran before the comment export. Comment objects may therefore already have been cached by PRAW. The 0.81-second export must not be presented as a cold-start end-to-end comment retrieval benchmark. No isolated retrieval-time or throughput claim is established by this run.

For a comparison against the earlier capped T1, distinguish the cap setting from changes in Reddit search availability over time. A contemporaneous capped control and inspection of exported thread IDs would be needed to attribute all count differences to the cap alone.

### Branch policy

Keep this experiment on `test/no-thread-cap`. **Do not merge it into `main`.** Retain the existing 200-submission safeguard for general use. The uncapped option remains an experimental mode for this evaluation.

Retain the run's Search Log JSON, Excel export and Early Report PDF with the research records, using a distinct `T7_NoCap` label. Those files are not included in this documentation-only update.
