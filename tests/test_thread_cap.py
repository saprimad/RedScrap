"""Offline retrieval tests using the application's real Scraper and GUI methods."""
import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import json
import threading
import time
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'RedScrap.py'
module = ast.parse(SOURCE.read_text(encoding='utf-8'))
ns = dict(datetime=datetime, timedelta=timedelta, timezone=timezone, time=time,
          threading=threading, json=json)
# Avoid importing optional GUI/NLP dependencies or prompting for credentials.
exec(compile(ast.Module(body=[n for n in module.body if isinstance(n, ast.ClassDef)
                            and n.name in {'Scraper', 'GUI'}], type_ignores=[]),
             str(SOURCE), 'exec'), ns)
Scraper, GUI = ns['Scraper'], ns['GUI']
STAMP = datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp()

class FakeReddit:
    def __init__(self, items, fail=False):
        self.items, self.fail, self.calls = items, fail, []
    def subreddit(self, name):
        return self
    def search(self, query, sort, limit):
        self.calls.append((query, sort, limit))
        for index, item in enumerate(self.items):
            if limit is not None and index >= limit:
                break
            yield item
        if self.fail:
            raise RuntimeError('simulated API interruption')

def items(n):
    return [SimpleNamespace(id=str(i), created_utc=STAMP, title=f'Thread {i}', num_comments=2)
            for i in range(n)]

def scraper(reddit):
    return Scraper(reddit, 'malaysia', ['langkawi'], '2024-10-29', '2026-10-29')

class RetrievalTests(unittest.TestCase):
    def test_no_cap_exceeds_200(self):
        r = FakeReddit(items(350)); s = scraper(r)
        self.assertEqual(len(s.fetch_threads(limit=None)), 350)
        self.assertIsNone(r.calls[0][2])
        self.assertEqual(s.search_metadata['status'], 'available_results_exhausted')
    def test_existing_default_cap(self):
        s = scraper(FakeReddit(items(350)))
        self.assertEqual(len(s.fetch_threads()), 200)
        self.assertEqual(s.search_status, 'user_cap_reached')
        self.assertTrue(s.search_limit_reached)
    def test_date_filter_and_duplicate_ids(self):
        data = items(3); data.append(data[0])
        data.append(SimpleNamespace(id='outside', created_utc=0))
        s = scraper(FakeReddit(data))
        self.assertEqual(len(s.fetch_threads(None)), 3)
        self.assertEqual(s.search_duplicate_count, 1)
        self.assertEqual(s.search_retrieved_count, 5)
    def test_end_date_inclusive(self):
        end = datetime(2026,10,29,23,59,59,tzinfo=timezone.utc).timestamp()
        data = [SimpleNamespace(id='last-second',created_utc=end),
                SimpleNamespace(id='next-day',created_utc=end+1)]
        self.assertEqual(len(scraper(FakeReddit(data)).fetch_threads(None)), 1)
    def test_cancellation_retains_partial_results(self):
        s = scraper(FakeReddit(items(350)))
        calls = 0
        def cancel():
            nonlocal calls
            calls += 1
            return calls > 20
        self.assertEqual(len(s.fetch_threads(None, cancel)), 10)
        self.assertEqual(s.search_status, 'cancelled')
    def test_failure_is_not_reported_as_exhaustion(self):
        s = scraper(FakeReddit(items(3), fail=True))
        with self.assertRaises(RuntimeError): s.fetch_threads(None)
        self.assertEqual(len(s.posts), 3)
        self.assertEqual(s.search_metadata['status'], 'api_or_error_interruption')
    def test_empty_results(self):
        s = scraper(FakeReddit([])); self.assertEqual(s.fetch_threads(None), [])
        self.assertEqual(s.search_status, 'available_results_exhausted')
    def test_invalid_cap(self):
        for value in [0,-1,True,1.5]:
            with self.assertRaises(ValueError): scraper(FakeReddit([])).fetch_threads(value)

class Widget:
    def __init__(self, value=''): self.value=value; self.state='normal'
    def get(self): return self.value
    def config(self, **kwargs): self.__dict__.update(kwargs)
    def delete(self,*args): pass
    def insert(self,*args): pass

class GuiTests(unittest.TestCase):
    def test_gui_forwards_both_modes_and_restores_controls(self):
        ns['tk'] = SimpleNamespace(DISABLED='disabled',NORMAL='normal',END='end')
        ns['messagebox'] = SimpleNamespace(showerror=lambda *a: self.fail(str(a)),showwarning=lambda *a: None)
        for uncapped, expected in [(False,200),(True,350)]:
            g=GUI.__new__(GUI); g.search_in_progress=False; g.reddit=FakeReddit(items(350))
            g.subreddit_entry=Widget('malaysia'); g.keyword_entry=Widget('langkawi')
            g.start_entry=Widget('2024-10-29'); g.end_entry=Widget('2026-10-29')
            g.no_thread_cap=Widget(uncapped); g.progress=None
            for name in ['search_button','no_cap_checkbox','search_log_button','report_btn',
                         'scrape_selected_btn','scrape_all_btn','listbox','summary_label']:
                setattr(g,name,Widget())
            callbacks=[]; g.root=SimpleNamespace(after=lambda delay,fn: callbacks.append(fn))
            g._entry_value=lambda entry: entry.get(); g.log_message=lambda *a: None
            g.update_summary=lambda: None
            g.search_threads()
            deadline=time.monotonic()+3
            while g.search_in_progress and time.monotonic()<deadline:
                if callbacks: callbacks.pop(0)()
                time.sleep(.001)
            self.assertFalse(g.search_in_progress)
            self.assertEqual(len(g.posts),expected)
            self.assertEqual(g.search_button.state,'normal')
            self.assertEqual(g.search_metadata['matching_threads'],expected)
            self.assertEqual(g.reddit.calls[0][2],None if uncapped else 200)

if __name__ == '__main__': unittest.main()
