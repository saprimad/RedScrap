"""Local two-stage relevance/sentiment training, evaluation and prediction.

No Reddit credentials are required. Only load trusted .rsmodel files: joblib
uses Python pickle and can execute code before a file can be validated.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import platform

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline

RELEVANCE = ('Related', 'Not related')
SENTIMENT = ('Positive', 'Negative', 'Neutral')
SCHEMA_VERSION = 1
MARKERS = {'[deleted]', '[removed]', '[ removed by reddit ]'}


def normalise(text):
    return ' '.join(str(text).strip().casefold().split())


def readable(text):
    return bool(normalise(text)) and normalise(text) not in MARKERS


def read_data(path):
    """Read comment text literally, including cells beginning with '='."""
    path = Path(path)
    if path.suffix.lower() == '.csv':
        df = pd.read_csv(path, keep_default_na=False, dtype=str)
    elif path.suffix.lower() == '.xlsx':
        import openpyxl
        book = openpyxl.load_workbook(path, read_only=True, data_only=False)
        try:
            rows = list(book.active.values)
        finally:
            book.close()
        if not rows:
            raise ValueError('The workbook is empty.')
        df = pd.DataFrame(rows[1:], columns=rows[0]).fillna('')
    else:
        raise ValueError('Choose a .csv or .xlsx dataset.')
    if df.empty:
        raise ValueError('The dataset has no rows.')
    if df.columns.duplicated().any() or any(c is None for c in df.columns):
        raise ValueError('Column names must be present and unique.')
    return df


def write_excel(frame, path):
    """Write all strings explicitly as text, never executable spreadsheet formulas."""
    import openpyxl
    from openpyxl.cell import WriteOnlyCell
    if Path(path).suffix.lower() != '.xlsx':
        raise ValueError('Output must use the .xlsx extension.')
    book = openpyxl.Workbook(write_only=True)
    sheet = book.create_sheet('Comments')
    for values in [list(frame.columns)]:
        cells = []
        for value in values:
            cell = WriteOnlyCell(sheet, value=str(value)); cell.data_type = 's'; cells.append(cell)
        sheet.append(cells)
    for values in frame.itertuples(index=False, name=None):
        cells = []
        for value in values:
            if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
                value = ''
            # Excel cannot hold text longer than 32767 characters: fail instead of truncating.
            if isinstance(value, str) and len(value) > 32767:
                raise ValueError('A cell exceeds Excel\'s 32,767-character limit. Shorten it before export.')
            cell = WriteOnlyCell(sheet, value=value)
            if isinstance(value, str): cell.data_type = 's'
            cells.append(cell)
        sheet.append(cells)
    book.save(path)


def make_template(frame, text_column='Comment'):
    if text_column not in frame:
        raise ValueError(f'Missing text column: {text_column}')
    if 'Relevance' in frame or 'Sentiment' in frame:
        raise ValueError('Dataset already has Relevance or Sentiment columns; use that labelled file instead.')
    result = frame.copy()
    result['Relevance'] = ''
    result['Sentiment'] = ''
    return result


def _pipeline():
    # Character n-grams avoid an English stop list and accept short/non-Latin text.
    # This is language-agnostic preprocessing, not evidence of multilingual validity.
    return Pipeline([
        ('tfidf', TfidfVectorizer(analyzer='char', ngram_range=(2, 5), max_features=20000, sublinear_tf=True)),
        ('classifier', LogisticRegression(C=1.0, class_weight='balanced', max_iter=2000, random_state=42)),
    ])


def _label(value, choices):
    lookup = {v.casefold(): v for v in choices}
    return lookup.get(str(value).strip().casefold())


def _metrics(truth, predictions, labels):
    return {
        'n': len(truth),
        'accuracy': float(accuracy_score(truth, predictions)),
        'macro_f1': float(f1_score(truth, predictions, labels=list(labels), average='macro', zero_division=0)),
        'per_class': classification_report(truth, predictions, labels=list(labels), output_dict=True, zero_division=0),
        'confusion_matrix_labels': list(labels),
        'confusion_matrix': confusion_matrix(truth, predictions, labels=list(labels)).tolist(),
    }


def train_models(frame, topic, text_column='Comment', group_column=None, seed=42, test_size=0.25):
    """Hold out rows/whole threads before fitting vectorisers or classifiers.

    Duplicate normalised texts are removed before splitting, conflicting labels
    rejected, and thread grouping used automatically when Thread URL is present.
    Saved estimators remain fitted on the training partition, not the hold-out.
    """
    if not str(topic).strip():
        raise ValueError('Describe the research topic used to decide relevance.')
    for col in (text_column, 'Relevance', 'Sentiment'):
        if col not in frame: raise ValueError(f'Missing column: {col}')
    if not 0.1 <= test_size <= 0.5: raise ValueError('Test fraction must be between 0.1 and 0.5.')
    data = frame.copy().fillna('')
    data['_text'] = data[text_column].astype(str)
    if not data['_text'].map(readable).all():
        raise ValueError('Training rows must contain text; remove blank/deleted/removed rows before labelling.')
    data['_relevance'] = data['Relevance'].map(lambda x: _label(x, RELEVANCE))
    if data['_relevance'].isna().any(): raise ValueError('Every training row needs Related or Not related.')
    related = data['_relevance'].eq('Related')
    data['_sentiment'] = data['Sentiment'].map(lambda x: _label(x, SENTIMENT))
    if data.loc[related, '_sentiment'].isna().any():
        raise ValueError('Every Related row needs Positive, Negative or Neutral.')
    if data.loc[~related, 'Sentiment'].astype(str).str.strip().ne('').any():
        raise ValueError('Leave Sentiment blank for Not related rows.')
    data['_key'] = data['_text'].map(normalise)
    for _, same in data.groupby('_key', sort=False):
        labels = set(zip(same['_relevance'], same['_sentiment'].fillna('')))
        if len(labels) > 1: raise ValueError('The same comment text has conflicting labels. Resolve them before training.')
    before = len(data)
    data = data.drop_duplicates('_key').reset_index(drop=True)
    strata = data['_sentiment'].where(data['_relevance'].eq('Related'), 'Not related')
    counts = strata.value_counts()
    if any(counts.get(c, 0) < 5 for c in (*SENTIMENT, 'Not related')):
        raise ValueError('Provide at least 5 distinct texts for each of Positive, Negative, Neutral and Not related (more is recommended).')
    if group_column is None and 'Thread URL' in data:
        group_column = 'Thread URL'
    if group_column:
        if group_column not in data or data[group_column].astype(str).str.strip().eq('').any():
            raise ValueError('The grouping column must exist and be non-empty for every training row.')
        groups = data[group_column].astype(str).str.strip()
        if groups.nunique() < 2: raise ValueError('At least two independent groups are needed for a held-out test.')
        splitter = GroupShuffleSplit(n_splits=100, test_size=test_size, random_state=seed)
        candidates = splitter.split(data, groups=groups)
        split_kind = f'whole groups: {group_column}'
    else:
        candidates = [train_test_split(np.arange(len(data)), test_size=test_size, stratify=strata, random_state=seed)]
        split_kind = 'stratified distinct comment texts'
    wanted = set((*SENTIMENT, 'Not related'))
    for train, test in candidates:
        if set(strata.iloc[train]) == wanted and set(strata.iloc[test]) == wanted: break
    else:
        raise ValueError('Cannot hold out groups while retaining every class in train and test. Add independently labelled threads/classes.')
    training, heldout = data.iloc[train], data.iloc[test]
    rel = _pipeline().fit(training['_text'], training['_relevance'])
    related_train = training['_relevance'].eq('Related')
    sent = _pipeline().fit(training.loc[related_train, '_text'], training.loc[related_train, '_sentiment'])
    rel_predictions = rel.predict(heldout['_text'])
    true_related = heldout['_relevance'].eq('Related')
    sent_predictions = sent.predict(heldout.loc[true_related, '_text'])
    # End-to-end test includes relevance mistakes, not just sentiment on known Related rows.
    combined = np.array(['Not related'] * len(heldout), dtype=object)
    predicted_related = rel_predictions == 'Related'
    if predicted_related.any(): combined[predicted_related] = sent.predict(heldout.loc[predicted_related, '_text'])
    truth_combined = heldout['_sentiment'].where(true_related, 'Not related')
    evaluation = {
        'relevance': _metrics(heldout['_relevance'], rel_predictions, RELEVANCE),
        'sentiment_given_true_related': _metrics(heldout.loc[true_related, '_sentiment'], sent_predictions, SENTIMENT),
        'end_to_end': _metrics(truth_combined, combined, (*SENTIMENT, 'Not related')),
    }
    fingerprint = hashlib.sha256(data[['_key', '_relevance', '_sentiment']].fillna('').to_csv(index=False).encode()).hexdigest()
    metadata = {
        'topic': str(topic).strip(), 'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'text_column': text_column, 'group_column': group_column, 'split_method': split_kind,
        'random_seed': seed, 'requested_test_fraction': test_size,
        'training_rows': len(train), 'test_rows': len(test), 'distinct_labelled_rows': len(data),
        'duplicates_removed': before - len(data), 'class_counts': {str(k): int(v) for k, v in counts.items()},
        'labelled_data_sha256': fingerprint, 'python_version': platform.python_version(),
        'sklearn_version': sklearn.__version__, 'evaluation': evaluation,
        'training_note': 'Both saved pipelines are fitted only on the training partition. Test rows are not used for fitting or vectoriser vocabulary.',
        'limitations': 'Internal held-out evaluation only. No claim of general accuracy across languages/topics; human labels and external validation remain necessary.',
    }
    # Store hashes, not raw training text, in the audit so leakage is inspectable.
    audit = {'train_text_sha256': [hashlib.sha256(s.encode()).hexdigest() for s in training['_key']],
             'test_text_sha256': [hashlib.sha256(s.encode()).hexdigest() for s in heldout['_key']]}
    if group_column:
        audit.update(train_groups_sha256=sorted({hashlib.sha256(s.encode()).hexdigest() for s in groups.iloc[train]}),
                     test_groups_sha256=sorted({hashlib.sha256(s.encode()).hexdigest() for s in groups.iloc[test]}))
    return {'format': 'RedScrap two-stage sentiment', 'schema_version': SCHEMA_VERSION,
            'relevance_model': rel, 'sentiment_model': sent, 'metadata': metadata, 'split_audit': audit}


def save_bundle(bundle, path):
    if Path(path).suffix.lower() != '.rsmodel': raise ValueError('Save the model with a .rsmodel extension.')
    validate_bundle(bundle)
    joblib.dump(bundle, path)


def validate_bundle(bundle):
    if not isinstance(bundle, dict) or bundle.get('format') != 'RedScrap two-stage sentiment' or bundle.get('schema_version') != SCHEMA_VERSION:
        raise ValueError('Not a supported RedScrap two-stage model bundle.')
    metadata = bundle.get('metadata', {})
    if metadata.get('sklearn_version') != sklearn.__version__:
        raise ValueError(f"Model requires scikit-learn {metadata.get('sklearn_version')}; installed version is {sklearn.__version__}.")
    for key, labels in [('relevance_model', RELEVANCE), ('sentiment_model', SENTIMENT)]:
        estimator = bundle.get(key)
        if not isinstance(estimator, Pipeline) or not hasattr(estimator, 'classes_') or set(estimator.classes_) != set(labels):
            raise ValueError(f'Invalid fitted pipeline or label set: {key}')
    if not str(metadata.get('topic', '')).strip(): raise ValueError('The model has no research topic.')
    return bundle


def load_bundle(path):
    """Trusted local files only: validation cannot make unpickling untrusted data safe."""
    return validate_bundle(joblib.load(path))


def predict_comments(bundle, frame, text_column='Comment'):
    validate_bundle(bundle)
    if text_column not in frame: raise ValueError(f'Missing text column: {text_column}')
    reserved = ['Predicted relevance', 'Predicted sentiment', 'Analysis status']
    if any(c in frame for c in reserved): raise ValueError('Prediction columns already exist; choose the original unclassified dataset.')
    out = frame.copy().reset_index(drop=True)
    text = out[text_column].fillna('').astype(str)
    eligible = text.map(readable)
    out['Predicted relevance'] = ''
    out['Predicted sentiment'] = ''
    out['Analysis status'] = 'Unavailable or blank text'
    if eligible.any():
        out.loc[eligible, 'Predicted relevance'] = bundle['relevance_model'].predict(text.loc[eligible])
        out.loc[eligible, 'Analysis status'] = 'Classified'
        keep = out['Predicted relevance'].eq('Related')
        if keep.any(): out.loc[keep, 'Predicted sentiment'] = bundle['sentiment_model'].predict(text.loc[keep])
    relevant = out['Predicted relevance'].eq('Related')
    counts = {label: int(out.loc[relevant, 'Predicted sentiment'].eq(label).sum()) for label in SENTIMENT}
    n = int(relevant.sum())
    summary = {
        'total_rows': len(out), 'analysed_rows': int(eligible.sum()),
        'related': n, 'not_related': int(out['Predicted relevance'].eq('Not related').sum()),
        'unavailable_or_blank': int((~eligible).sum()), 'counts': counts,
        'percentages': {k: v / n * 100 if n else 0.0 for k, v in counts.items()},
        'sentiment_denominator': n, 'topic': bundle['metadata']['topic'],
    }
    return out, summary


def write_report(bundle, summary, path):
    """Export an aggregate PDF with model provenance, denominators and test metrics."""
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    from reportlab.lib.pagesizes import letter
    if Path(path).suffix.lower() != '.pdf': raise ValueError('Report output must use the .pdf extension.')
    styles = getSampleStyleSheet(); story = []
    def para(s, style='BodyText'): story.append(Paragraph(html.escape(str(s)), styles[style])); story.append(Spacer(1, 8))
    meta = bundle['metadata']
    para('RedScrap relevance and sentiment report', 'Title')
    para('Research topic: ' + meta['topic'])
    para('Model trained: ' + meta['created_at_utc'])
    para('Labelled-data fingerprint: ' + meta['labelled_data_sha256'])
    para('Input rows: {total_rows}; analysed: {analysed_rows}; Related: {related}; Not related: {not_related}; unavailable/blank: {unavailable_or_blank}.'.format(**summary))
    para('Sentiment percentages use predicted Related comments only (n = '+str(summary['sentiment_denominator'])+'). Not related is a relevance label, not Neutral sentiment.')
    rows = [['Sentiment', 'Count', '% of Related']] + [[k, summary['counts'][k], f"{summary['percentages'][k]:.2f}%"] for k in SENTIMENT]
    table = Table(rows, colWidths=[190, 110, 140]); table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),.4,colors.grey)]));story.append(table);story.append(Spacer(1,12))
    para('Held-out evaluation', 'Heading2')
    para(f"Split: {meta['split_method']}; training rows: {meta['training_rows']}; test rows: {meta['test_rows']}; seed: {meta['random_seed']}. Saved models were fitted on training rows only.")
    stage_names = {'relevance': 'Relevance', 'sentiment_given_true_related': 'Sentiment on human-labelled Related test rows', 'end_to_end': 'End-to-end (including relevance errors)'}
    for stage, metrics in meta['evaluation'].items():
        caption = Paragraph(html.escape(f"{stage_names[stage]}: n = {metrics['n']}; accuracy = {metrics['accuracy']:.3f}; macro F1 = {metrics['macro_f1']:.3f}."), styles['BodyText'])
        labels = metrics['confusion_matrix_labels']
        cm = [['True / predicted', *labels]] + [[label, *row] for label, row in zip(labels, metrics['confusion_matrix'])]
        t = Table(cm, repeatRows=1);t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.3,colors.grey),('FONTSIZE',(0,0),(-1,-1),8)]));story.append(KeepTogether([caption, Spacer(1,8), t]));story.append(Spacer(1,10))
    para(meta['limitations'])
    para('Sentiment polarity does not measure acceptance, agreement or stance. Predictions require researcher review.')
    SimpleDocTemplate(str(path), pagesize=letter).build(story)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    template = sub.add_parser('template');template.add_argument('--input', required=True);template.add_argument('--output', required=True)
    train = sub.add_parser('train');train.add_argument('--input', required=True);train.add_argument('--topic', required=True);train.add_argument('--model', required=True);train.add_argument('--group-column');train.add_argument('--seed', type=int, default=42)
    predict = sub.add_parser('predict');predict.add_argument('--input', required=True);predict.add_argument('--model', required=True);predict.add_argument('--output', required=True);predict.add_argument('--report', required=True);predict.add_argument('--trust-model', action='store_true', help='Acknowledge that the model was created by you or obtained from a trusted source.')
    for command in (template, train, predict): command.add_argument('--text-column', default='Comment')
    args = parser.parse_args()
    try:
        if args.action == 'predict' and not args.trust_model: raise ValueError('Only load trusted models. Add --trust-model for a model you created or trust.')
        if args.action in ('template', 'predict') and Path(args.input).resolve() == Path(args.output).resolve():
            raise ValueError('Choose a new output filename; the source dataset must not be overwritten.')
        data = read_data(args.input)
        if args.action == 'template': write_excel(make_template(data, args.text_column), args.output)
        elif args.action == 'train':
            bundle = train_models(data, args.topic, args.text_column, args.group_column, args.seed)
            save_bundle(bundle, args.model)
            Path(str(args.model)+'.evaluation.json').write_text(json.dumps({'metadata':bundle['metadata'], 'split_audit':bundle['split_audit']}, indent=2), encoding='utf-8')
            print(json.dumps(bundle['metadata']['evaluation'], indent=2))
        else:
            bundle = load_bundle(args.model);out, summary = predict_comments(bundle, data, args.text_column)
            write_excel(out, args.output);write_report(bundle, summary, args.report)
            Path(str(args.output)+'.summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
            print(json.dumps(summary, indent=2))
    except (ValueError, OSError) as exc: parser.exit(2, str(exc)+'\n')


if __name__ == '__main__': main()
