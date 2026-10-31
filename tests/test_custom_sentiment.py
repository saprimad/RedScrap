import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import numpy as np
import openpyxl
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import custom_sentiment as cs


def labelled():
    rows = []
    for thread in range(12):
        for kind, sentence in [('Positive', 'The library service was helpful and excellent'),
                               ('Negative', 'The library service was awful and disappointing'),
                               ('Neutral', 'The library service opens on Monday'),
                               ('Not related', 'Football players scored a goal yesterday')]:
            rows.append({'Comment': f'{sentence}; sample {thread} {kind}',
                         'Thread URL': f'https://example.test/thread/{thread}',
                         'Relevance': 'Not related' if kind == 'Not related' else 'Related',
                         'Sentiment': '' if kind == 'Not related' else kind})
    return pd.DataFrame(rows)


class ModelWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = cs.train_models(labelled(), 'Views about a library service')

    def test_heldout_groups_and_text_do_not_overlap(self):
        audit = self.bundle['split_audit']
        self.assertFalse(set(audit['train_groups_sha256']) & set(audit['test_groups_sha256']))
        self.assertFalse(set(audit['train_text_sha256']) & set(audit['test_text_sha256']))
        self.assertEqual(len(audit['train_text_sha256']), self.bundle['metadata']['training_rows'])
        self.assertEqual(self.bundle['metadata']['evaluation']['end_to_end']['n'], self.bundle['metadata']['test_rows'])
        self.assertEqual(len(self.bundle['metadata']['evaluation']['end_to_end']['confusion_matrix']), 4)

    def test_roundtrip_models_and_metadata(self):
        data = pd.DataFrame({'Comment': ['The library is great', 'football match', '[deleted]', '']})
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'model.rsmodel';cs.save_bundle(self.bundle, p)
            loaded = cs.load_bundle(p)
            a, summary = cs.predict_comments(self.bundle, data)
            b, other = cs.predict_comments(loaded, data)
            pd.testing.assert_frame_equal(a,b);self.assertEqual(summary, other)
            self.assertEqual(summary['unavailable_or_blank'],2)
            self.assertFalse(loaded['metadata'].get('raw_training_text'))

    def test_relevance_gate_denominator_and_neutral(self):
        data = pd.DataFrame({'Comment':['good topic', 'off topic', 'plain topic', '[removed]', '']}, index=[2,9,10,20,30])
        with patch.object(self.bundle['relevance_model'], 'predict', return_value=np.array(['Related','Not related','Related'])), patch.object(self.bundle['sentiment_model'], 'predict', return_value=np.array(['Positive','Neutral'])) as sent:
            out, summary = cs.predict_comments(self.bundle, data)
        sent.assert_called_once()
        self.assertEqual(len(sent.call_args.args[0]),2)
        self.assertEqual(summary['not_related'],1)
        self.assertEqual(summary['sentiment_denominator'],2)
        self.assertEqual(summary['percentages'],{'Positive':50.0,'Negative':0.0,'Neutral':50.0})
        self.assertEqual(out.loc[1,'Predicted sentiment'],'')
        self.assertEqual(data.columns.tolist(),['Comment'])

    def test_all_irrelevant_and_empty_inputs(self):
        with patch.object(self.bundle['relevance_model'], 'predict', return_value=np.array(['Not related'])), patch.object(self.bundle['sentiment_model'], 'predict') as sent:
            _, s = cs.predict_comments(self.bundle, pd.DataFrame({'Comment':['unrelated text']}))
        sent.assert_not_called();self.assertEqual(s['related'],0);self.assertEqual(sum(s['counts'].values()),0)
        _, s = cs.predict_comments(self.bundle, pd.DataFrame({'Comment':[]}))
        self.assertEqual(s['total_rows'],0)

    def test_duplicate_texts_removed_and_conflicts_rejected(self):
        data=labelled();duplicate=data.iloc[[0]].copy();duplicate['Comment']='  '+duplicate['Comment'].iloc[0].upper()+'  '
        bundle=cs.train_models(pd.concat([data,duplicate],ignore_index=True),'Library')
        self.assertEqual(bundle['metadata']['duplicates_removed'],1)
        duplicate['Sentiment']='Negative'
        with self.assertRaisesRegex(ValueError,'conflicting'):
            cs.train_models(pd.concat([data,duplicate],ignore_index=True),'Library')

    def test_incomplete_labels_and_insufficient_data_fail(self):
        data=labelled();data.loc[0,'Sentiment']=''
        with self.assertRaisesRegex(ValueError,'Every Related'):cs.train_models(data,'Library')
        data=labelled();data.loc[0,'Relevance']='Maybe'
        with self.assertRaisesRegex(ValueError,'Every training'):cs.train_models(data,'Library')
        with self.assertRaisesRegex(ValueError,'at least 5'):cs.train_models(labelled().iloc[:8],'Library')
        with self.assertRaisesRegex(ValueError,'research topic'):cs.train_models(labelled(),'')

    def test_impossible_group_split_fails(self):
        data=labelled();data['Thread URL']=data['Sentiment'].replace('','Not related')
        with self.assertRaisesRegex(ValueError,'Cannot hold out groups'):cs.train_models(data,'Library')
        data.loc[0,'Thread URL']=''
        with self.assertRaisesRegex(ValueError,'non-empty'):cs.train_models(data,'Library')

    def test_ungrouped_split_and_invalid_model(self):
        b=cs.train_models(labelled().drop(columns='Thread URL'),'Library')
        self.assertEqual(b['metadata']['split_method'],'stratified distinct comment texts')
        with self.assertRaisesRegex(ValueError,'supported'):cs.validate_bundle({})
        b['metadata']['sklearn_version']='0.0.invalid'
        with self.assertRaisesRegex(ValueError,'requires scikit-learn'):cs.validate_bundle(b)

    def test_cli_does_not_overwrite_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'source.xlsx'
            cs.write_excel(pd.DataFrame({'Comment':['original text']}),source)
            before=source.read_bytes()
            with patch.object(sys,'argv',['custom_sentiment.py','template','--input',str(source),'--output',str(source)]):
                with self.assertRaises(SystemExit) as error:cs.main()
            self.assertEqual(error.exception.code,2)
            self.assertEqual(source.read_bytes(),before)

    def test_formula_like_text_roundtrip_and_output_pdf(self):
        data=pd.DataFrame({'Comment':['=1+1','[deleted]','normal text'], 'Author':['@formula','name','safe']})
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'comments.xlsx';cs.write_excel(cs.make_template(data), p)
            book=openpyxl.load_workbook(p,data_only=False)
            self.assertEqual(book.active['A2'].data_type,'s');self.assertEqual(book.active['A2'].value,'=1+1');book.close()
            restored=cs.read_data(p);self.assertEqual(restored.loc[0,'Comment'],'=1+1')
            out, summary=cs.predict_comments(self.bundle,data)
            report=Path(tmp)/'report.pdf';cs.write_report(self.bundle,summary,report)
            self.assertGreater(report.stat().st_size,1000)


class ApplicationIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Import without credentials or network; PRAW is only needed for live retrieval.
        sys.modules.setdefault('praw', types.SimpleNamespace(Reddit=object))
        spec=importlib.util.spec_from_file_location('redscrap_under_test',Path(__file__).resolve().parents[1]/'RedScrap.py')
        cls.app=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.app)
        cls.bundle=cs.train_models(labelled(),'Library')

    def test_analyzer_custom_model_and_early_report(self):
        comments=pd.DataFrame({'author':['a','b','c'],'body':['good library', 'football unrelated','[deleted]'], 'upvotes':[1,0,-1], 'created':pd.to_datetime(['2026-01-01']*3)})
        fake_comment=types.SimpleNamespace(author='a', body='good library',score=1,created_utc=1767225600)
        fake_forest=types.SimpleNamespace(replace_more=lambda limit:None,list=lambda:[fake_comment])
        post=types.SimpleNamespace(comments=fake_forest, created_utc=1767225600, num_comments=1,score=1,title='Library',url='https://example.test',permalink='/r/test/comments/a',is_self=True)
        with patch.object(self.app.Analyzer,'_collect_comments',return_value=comments.copy()):
            analyzer=self.app.Analyzer([post],custom_bundle=self.bundle)
        self.assertEqual(analyzer.custom_prediction_summary['unavailable_or_blank'],1)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'early.pdf'
            self.app.Exporter.generate_pdf_enhanced([post],analyzer,str(path),{'subreddit':'test','keywords':['library'],'start_date':'2026-01-01','end_date':'2026-01-01'})
            import pymupdf
            with pymupdf.open(path) as doc:text='\n'.join(p.get_text() for p in doc)
            self.assertIn('Researcher-trained two-stage model',text)
            self.assertIn('Not related',text)
            self.assertNotIn('Sentiment140-based',text)

    def test_default_mode_still_loads_supplied_model(self):
        with patch.object(self.app.Analyzer,'_collect_comments',return_value=pd.DataFrame(columns=['author','body','upvotes','created'])), patch.object(self.app.Analyzer,'load_sentiment_model',return_value=False) as load:
            analyzer=self.app.Analyzer([])
        load.assert_called_once();self.assertIsNone(analyzer.custom_prediction_summary)
        self.assertEqual(analyzer.sentiment_summary(),{})


if __name__=='__main__':unittest.main()
