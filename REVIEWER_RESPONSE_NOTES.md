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


---

## Reviewer A4 — Secure Reddit API credential storage

### Reviewer concern
The reviewer noted that Reddit API credentials were stored in plaintext and requested a safer credential-management approach.

### Software changes
- The Reddit `client_secret` is no longer persisted in plaintext inside `reddit_config.json`.
- RedScrap now uses Python `keyring` to store the client secret in the operating-system credential store when available.
- The local configuration file retains only non-secret settings such as `client_id` and `user_agent`.
- Existing installations with a legacy plaintext `client_secret` are migrated automatically on the next successful launch. RedScrap attempts to store the secret securely and rewrites the configuration file without the secret.
- Environment variables are supported as an alternative credential source.
- If no secure credential store or environment secret is available, RedScrap prompts for the secret for the current session rather than writing it back to plaintext storage.
- `requirements.txt` and the README were updated to document the revised credential workflow.

### Functional testing
Platform:
- Windows

Verification performed:
- RedScrap launched successfully after the credential migration.
- The application did not require repeated credential entry after migration.
- The resulting `reddit_config.json` contained only `client_id` and `user_agent`.
- No plaintext `client_secret` remained in the configuration file.

### Security interpretation
The revised approach materially reduces the risk of accidental disclosure through copied project folders, source repositories or local plaintext configuration files. Secure storage remains dependent on the security of the host operating-system account.

**Status: PASS**


---

## Reviewer B1 — Novelty and contribution

### Reviewer concern
The reviewer requested clearer articulation of the software's novelty and contribution, together with a comparison against existing Reddit data-collection approaches.

### Contribution framing
RedScrap is not positioned as a new Reddit API or as a novel analytical algorithm. Its principal contribution is the reduction of technical barriers to Reddit-based research for users with limited programming or computational expertise, particularly researchers in the social and health sciences.

The software integrates commonly required stages of Reddit-based research within a single graphical desktop workflow, including:
- subreddit and keyword searching;
- date filtering;
- thread and comment retrieval;
- structured Excel export;
- configurable lexical preprocessing;
- exploratory reporting; and
- optional sentiment classification.

This positioning distinguishes RedScrap from programmer-oriented workflows that require users to write API scripts, operate command-line tools or assemble separate data-processing pipelines.

### Role of the Early Report
The Early Report is intended as an exploratory orientation tool that helps researchers rapidly understand the broad characteristics of a retrieved dataset before committing to more intensive analysis.

It provides an initial overview of:
- thread volume;
- engagement patterns;
- temporal distribution;
- lexical patterns; and
- optional exploratory sentiment output.

The Early Report is not intended to replace formal qualitative, quantitative or mixed-method analytical procedures. Its purpose is to support familiarisation with the dataset, identification of potentially relevant patterns and assessment of whether the retrieved material is suitable for subsequent analysis.

### Planned manuscript revision
The manuscript will:
- make the low-barrier social- and health-science use case explicit;
- clarify the role of the Early Report as an orientation rather than final analytical tool; and
- add a comparison table contrasting RedScrap with existing Reddit data-collection approaches in terms of technical requirements, graphical accessibility, retrieval workflow, export options and built-in exploratory analysis.

### Comparison table finalised
The comparison was refined against four representative approaches:
- **PRAW** — flexible Python API wrapper that requires Python knowledge for routine use.
- **praw-cli** — command-line Reddit extraction with strong filtering, export and reproducibility features.
- **Reddit Data Tool** — lightweight browser-based thread export using public Reddit JSON rather than OAuth/API client access.
- **Communalytic** — no-code computational social-science platform with Reddit collectors.

The comparison avoids claiming that RedScrap is the only low-code/no-code Reddit research tool. Instead, RedScrap is positioned as a focused local desktop workflow combining API-based retrieval, structured Excel export, researcher-configurable lexical preprocessing and an Early Report intended for rapid dataset orientation before more intensive analysis.

**Status: PASS — contribution clarified and comparison table added to README; manuscript table to use the same evidence-based positioning.**
