# Reviewer Response Notes

This file documents software changes and functional checks performed in response to reviewer comments on the RedScrap manuscript. It is intended as an internal revision audit trail and does not replace the manuscript response letter.

## Reviewer A1 — Search retrieval limit and date filtering

### Reviewer concern
RedScrap retrieves a maximum of 200 Reddit search results before applying the selected date range. This may cause older posts within the requested period to be missed without the user realising that the search is incomplete.

### Software changes
- Added tracking of the number of Reddit submissions examined during a search.
- Added a date-aware completeness check.
- A warning is displayed only when:
  - the configured 200-submission retrieval cap is reached; and
  - the oldest retrieved submission has not yet reached the user's selected start date.
- Added search diagnostics to the GUI summary, including:
  - number of submissions examined; and
  - whether the search-limit warning condition was triggered.
- Updated the warning text to explain that older posts within the requested date range may be missing and that narrower keywords or date ranges may improve coverage.

### Functional testing
Environment: Windows / VS Code / Python.

Test case:
- Subreddit: `r/malaysia`
- Keyword: `Langkawi`

Observed scenarios:
1. **2026-only search**
   - 71 matching threads were returned.
   - 200 submissions were examined by the search process.
   - No completeness warning was displayed because the retrieval had already crossed the selected start-date boundary.

2. **2020–2026 search**
   - 200 matching threads were returned.
   - The search reached the configured 200-submission cap before reaching the selected start date.
   - The **Search limit reached** warning was displayed as intended.

### Verification
- `python -m py_compile RedScrap.py` completed without error.
- GUI launch completed successfully.
- Date-aware warning behaviour matched the intended design.

**Status: PASS**

---

## Reviewer A2 — Sentiment-analysis warning and interpretation

### Reviewer concern
The sentiment model was trained using Sentiment140 (Twitter data), whereas RedScrap is applied to Reddit discussions. Users should be clearly warned that sentiment classifications are exploratory and have not been validated for Reddit data.

### Software changes
- Replaced the previous softer note with an explicit **Caution** statement in the generated PDF report.
- The report now states that the sentiment model:
  - uses a TF-IDF vectorizer and logistic-regression classifier;
  - was trained on the Sentiment140 Twitter dataset;
  - has not been externally validated for Reddit discourse;
  - has not been externally validated for Malay-language content or the present dataset; and
  - should be treated as exploratory rather than as a validated measure of opinion or stance.
- Added a recommendation for human review before drawing substantive conclusions, particularly for sarcasm, slang, code-switching and other context-dependent expressions.
- Reworded the automatic narrative to remain descriptive rather than inferential.
  - Removed statements such as `Overall sentiment leans positive` or `Overall sentiment leans negative`.
  - Replaced them with descriptive wording such as `A larger proportion of comments was classified as positive than negative.`

### Functional testing
- Generated a new RedScrap Early Report PDF from the updated branch.
- Verified that:
  - the old `Overall sentiment leans ...` wording no longer appeared;
  - the revised **Caution** statement appeared in the sentiment section;
  - the report explicitly stated the lack of external validation for Reddit and Malay-language content; and
  - the human-review recommendation was present.

### Verification
- PDF report generation completed successfully.
- Revised sentiment wording appeared as intended.

**Status: PASS**

---

## Branch and revision context

Reviewer A1 changes were developed in:
- `reviewer-a1-search-limit-warning`

Reviewer A2 changes were developed on top of A1 in:
- `reviewer-a2-sentiment-warning`

The A2 branch therefore contains both the tested A1 and A2 revisions prior to merge into `main`.


---

## Reviewer A3 / Reviewer B2 — Malay rationale and configurable lexical preprocessing

### Reviewer concerns
Reviewer A3 requested a clearer explanation for including Malay alongside English. Reviewer B2 noted that the previous wording could imply broader multilingual NLP capabilities than were actually implemented.

### Rationale and software changes
- The original Malay stop-word handling arose from iterative development and early testing in the Malaysian context, where common Malay function words were observed to contribute lexical noise and reduce the interpretability of word-frequency outputs.
- Added a **Lexical Settings** dialog to the GUI.
- Researchers can now:
  - enable or disable the built-in English stop-word list;
  - enable or disable the built-in Malay stop-word list; and
  - paste additional study-specific stop words, either comma-separated or one per line.
- The custom settings affect lexical word-frequency output only and do not alter the raw exported Reddit text.
- Documentation now explicitly distinguishes configurable lexical preprocessing from full multilingual NLP. RedScrap does not currently perform automatic language identification, stemming or lemmatisation.

### Functional testing
Test corpus:
- Subreddit: `r/malaysia`
- Keyword: `Langkawi`

A baseline Early Report showed generic high-frequency terms including:
`there, like, what, all, when, who, even, get, some, then, about, want, why, time, think, out, here`.

These terms were entered into **Lexical Settings → Additional stop words** and the report was regenerated. The specified terms no longer appeared in the Top 20 word-frequency output, while potentially meaningful terms such as `langkawi`, `malaysia`, `people`, `good`, `japanese` and `need` remained.

### Verification
- `python -m py_compile RedScrap.py` completed without error.
- Lexical Settings dialog opened successfully.
- English and Malay defaults were enabled as intended.
- Custom stop-word entry accepted comma-separated terms.
- Regenerated PDF reflected the custom lexical filtering.

**Status: PASS**
