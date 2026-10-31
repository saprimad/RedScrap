# No user-defined thread cap test

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
2. Tick **No user-defined limit**, then **Search Threads**. Unticked retains the previous 200-submission cap.
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
