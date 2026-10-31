# Researcher-trained relevance and sentiment (experimental branch)

This branch adds a local workspace for human labelling, two-stage model training,
held-out evaluation, saved model reuse, Excel predictions and PDF summaries.
It is not part of the archived v21.9.0 release. Nothing has been merged to main.
The existing 200-submission search safeguard is retained.

## Start without Reddit credentials

Install the repository requirements, then run:

```sh
python custom_sentiment_gui.py
```

Or start RedScrap normally and select **Sentiment Workspace**. Collection and
raw Excel export do not require training a model. The supplied binary model
remains the default for Early Report unless a custom model is explicitly selected.

## Research workflow

1. **Select dataset**: an existing RedScrap `.xlsx` export or UTF-8 `.csv`.
2. **Create labelling template**: choose a new `.xlsx` file. The original columns
   remain, with blank **Relevance** and **Sentiment** columns appended.
3. Define a clear research topic and labelling guide. Human reviewers assign
   **Related** or **Not related** relative to that topic. Only Related rows receive
   **Positive**, **Negative** or **Neutral**. Not related is not Neutral.
4. Select the labelled file. Remove unavailable/blank rows and unlabelled rows
   from the training copy. There must be at least five distinct texts for EACH
   sentiment and for Not related. This is a technical minimum, not a recommended
   research sample size or evidence of model quality.
5. **Train models**: enter the topic and text column (default **Comment**). Save a
   `.rsmodel` file. The JSON alongside it records metrics and split hashes.
6. Review accuracy, macro F1, per-class precision/recall/F1/support and confusion
   matrices in the evaluation JSON. The GUI shows this JSON after training.
7. Select another unclassified dataset and **Classify and export**. This creates a
   new Excel file, aggregate PDF and summary JSON. It preserves source rows and
   columns, adding **Predicted relevance**, **Predicted sentiment** and
   **Analysis status**. Predicted Not related rows retain a blank sentiment.
8. In the integrated workspace, **Use model in Early Report** selects the loaded
   custom model for subsequent reports in this session. The report states its
   topic, provenance, internal test metrics and counting bases. **Use supplied
   model in Early Report** restores the legacy binary model. This selection does
   not replace the supplied model files or change previous reports.

Sentiment percentages use predicted Related comments ONLY. Not related and
unavailable/blank text are counted separately. No comments are deleted from the
prediction export. Topic-specific relevance still requires user-labelled examples;
entering a topic alone does not teach the classifier its meaning.

## Evaluation and scope

Both stages use separate scikit-learn pipelines: character 2–5-gram TF-IDF
(maximum 20,000 features, sublinear term frequency, no language stop list), then
class-balanced logistic regression (C=1, max_iter=2000). This preprocessing
accepts diverse text, including non-Latin scripts; it does not establish
multilingual predictive validity.

The default test fraction is 25% (seed 42). Exact normalised text duplicates
(casefolded and whitespace-collapsed) are removed before splitting; conflicting
labels fail explicitly. If **Thread URL** is present, entire thread groups are
kept together, and every row must have a non-empty group. Up to 100 deterministic
candidate group splits are considered for class coverage only, not performance.
All four combined classes must occur in both partitions. Otherwise training
stops with a request for more independently labelled threads/classes. Data without
a Thread URL use a stratified split of distinct comment texts. The Python API
and CLI optionally accept another grouping column.

Vectoriser vocabularies and BOTH classifiers are fitted on training rows only.
The saved pipelines are those tested estimators; they are NOT refitted on all
labelled rows after evaluation. Reported measures distinguish:

- relevance on all held-out comments;
- sentiment on held-out comments human-labelled Related (conditional stage score);
- end-to-end four-category predictions, including errors from relevance gating.

These are internal test results. Repeated authors, near-duplicates, annotation
errors and domain drift can still bias evaluation. Choose a grouping unit suited
to the study, review human agreement and assess independent data before claiming
predictive validity. Sentiment polarity is not acceptance, agreement or stance.

## Saved models and reproducibility

The `.rsmodel` bundle contains BOTH fitted pipelines plus the topic, label-data
fingerprint, counts, seed, split method, test metrics and Python/scikit-learn
versions. Split audit entries contain hashes rather than raw comment text or
thread URLs. Models still encode learned vocabulary: treat them as research
artefacts, not automatically anonymised data.

Training is deterministic for a fixed dataset/order, seed and package environment;
creation timestamps naturally differ. Keep original labelled data, model,
evaluation JSON, versions and topic/annotation guide together. A changed input,
package version or new Reddit scrape is not expected to reproduce the old output.
Loading requires the exact recorded scikit-learn version. The repository currently
pins scikit-learn 1.7.2 for the supplied binary models; train and load within the
same installed environment.

Joblib/pickle files can execute code WHEN LOADED. Only load files you created or
trust; validation after loading cannot make an untrusted file safe. The GUI
requires an explicit trust checkbox and the CLI requires `--trust-model`.
Data and models stay on the user's device; no remote AI service is called.

## CLI

```sh
python custom_sentiment.py template --input Comments.xlsx --output Comments_to_label.xlsx
python custom_sentiment.py train --input Comments_labelled.xlsx --topic "Views about a library service" --model library.rsmodel
python custom_sentiment.py predict --input Other_comments.xlsx --model library.rsmodel --trust-model --output Comments_classified.xlsx --report Sentiment_report.pdf
```

Add `--text-column` if the text column is not named Comment. Training optionally
accepts `--group-column` and `--seed`. Outputs should use NEW filenames.

`examples/labelled_comments.csv` contains SYNTHETIC examples for testing the
workflow only. Its scores are not validation evidence for Reddit or real research.
No real research comments, model binaries or credentials are committed here.

## Checks

```sh
python -m unittest discover -s tests -v
python -m py_compile RedScrap.py custom_sentiment.py custom_sentiment_gui.py
```

This feature should be described in a paper as experimental development until it
has been reviewed and tested on suitable real data. Existing paper results are not
retroactively results from this module.
