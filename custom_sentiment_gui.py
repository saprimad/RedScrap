"""Offline graphical workspace for researcher-labelled relevance and sentiment."""
from __future__ import annotations

import json
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

from custom_sentiment import (load_bundle, make_template, predict_comments, read_data,
                              save_bundle, train_models, write_excel, write_report)


class SentimentWorkspace:
    def __init__(self, parent=None, on_select=None):
        self.window = tk.Toplevel(parent) if parent is not None else tk.Tk()
        self.window.title('RedScrap - Relevance and Sentiment Workspace')
        self.window.geometry('820x650')
        self.on_select = on_select
        self.bundle = None
        self.input_path = None
        self.events = queue.Queue()
        self.busy = False
        self.buttons = []
        tk.Label(self.window, text='1. Label relevance.  2. Label sentiment for Related comments only.', font=('Arial', 12, 'bold')).pack(pady=8)
        tk.Label(self.window, text='Related / Not related     |     Positive / Negative / Neutral').pack()
        tk.Label(self.window, text='Research topic used to decide relevance:').pack(anchor='w', padx=12, pady=(12, 0))
        self.topic = tk.Entry(self.window);self.topic.pack(fill='x', padx=12)
        tk.Label(self.window, text='Text column (default: Comment):').pack(anchor='w', padx=12, pady=(8, 0))
        self.column = tk.Entry(self.window);self.column.insert(0, 'Comment');self.column.pack(fill='x', padx=12)
        self.file_label = tk.Label(self.window, text='No dataset selected', anchor='w', wraplength=780)
        self.file_label.pack(fill='x', padx=12, pady=8)
        frame = tk.Frame(self.window);frame.pack(pady=4)
        for label, action in [('Select dataset', self.select_input), ('Create labelling template', self.template), ('Train models', self.train)]:
            self.button(frame, label, action)
        self.trust = tk.BooleanVar(value=False)
        tk.Checkbutton(self.window, text='I created or trust the model file. Pickle-based model files can execute code when loaded.', variable=self.trust, wraplength=780).pack(padx=12, pady=8)
        frame = tk.Frame(self.window);frame.pack(pady=4)
        self.button(frame, 'Load trusted model', self.load)
        self.button(frame, 'Classify and export', self.predict)
        if on_select is not None:
            frame = tk.Frame(self.window);frame.pack(pady=4)
            self.button(frame, 'Use model in Early Report', self.use_model)
            self.button(frame, 'Use supplied model in Early Report', self.use_supplied)
        self.status = tk.Label(self.window, text='Ready. No Reddit credentials are needed in this workspace.', wraplength=780)
        self.status.pack(padx=12, pady=8)
        self.details = tk.Text(self.window, height=12, wrap='word', state='disabled')
        self.details.pack(fill='both', expand=True, padx=12, pady=(0, 12))
        self.window.after(100, self.poll)

    def button(self, frame, label, action):
        b = tk.Button(frame, text=label, command=action);b.pack(side='left', padx=4);self.buttons.append(b)

    def show(self, text):
        self.details.configure(state='normal');self.details.delete('1.0', 'end');self.details.insert('end', str(text));self.details.configure(state='disabled')

    def select_input(self):
        path = filedialog.askopenfilename(parent=self.window, filetypes=[('Datasets', '*.xlsx *.csv')])
        if path:self.input_path = path;self.file_label.configure(text=path)

    def require_input(self):
        if self.input_path is None:messagebox.showerror('Dataset required', 'Select an Excel or CSV dataset first.', parent=self.window);return False
        return True

    def run_job(self, description, work, done):
        if self.busy:return
        self.busy = True
        for b in self.buttons:b.configure(state='disabled')
        self.status.configure(text=description)
        def worker():
            try:self.events.put((True, work(), done))
            except Exception as exc:self.events.put((False, str(exc), None))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            ok, result, done = self.events.get_nowait()
        except queue.Empty:pass
        else:
            self.busy = False
            for b in self.buttons:b.configure(state='normal')
            if ok:
                self.status.configure(text='Completed.');done(result)
            else:
                self.status.configure(text='Operation failed.');messagebox.showerror('Relevance and sentiment', result, parent=self.window)
        self.window.after(100, self.poll)

    def template(self):
        if not self.require_input():return
        output = filedialog.asksaveasfilename(parent=self.window, initialfile='Comments_to_label.xlsx', defaultextension='.xlsx', filetypes=[('Excel', '*.xlsx')])
        if not output:return
        source, col = self.input_path, self.column.get().strip()
        if Path(output).resolve() == Path(source).resolve():
            messagebox.showerror('Choose a new file', 'The template must not overwrite the source dataset.', parent=self.window);return
        def work():write_excel(make_template(read_data(source), col), output);return output
        self.run_job('Creating template...', work, lambda path:self.show('Saved: '+path+'\nFill Relevance for each training row. Fill Sentiment only for Related rows. Remove unavailable/blank rows and leave no unlabelled training rows.'))

    def train(self):
        if not self.require_input():return
        topic, col, source = self.topic.get().strip(), self.column.get().strip(), self.input_path
        if not topic:messagebox.showerror('Topic required', 'Describe the research topic before training.', parent=self.window);return
        output = filedialog.asksaveasfilename(parent=self.window, initialfile='research_sentiment.rsmodel', defaultextension='.rsmodel', filetypes=[('RedScrap model', '*.rsmodel')])
        if not output:return
        def work():
            bundle = train_models(read_data(source), topic, col)
            save_bundle(bundle, output)
            Path(output+'.evaluation.json').write_text(json.dumps({'metadata':bundle['metadata'], 'split_audit':bundle['split_audit']}, indent=2), encoding='utf-8')
            return bundle
        self.run_job('Training and evaluating on a held-out partition...', work, self.set_bundle)

    def set_bundle(self, bundle):
        self.bundle = bundle
        self.show(json.dumps(bundle['metadata'], indent=2))
        self.status.configure(text='Model ready. Topic: '+bundle['metadata']['topic'])

    def load(self):
        if not self.trust.get():
            messagebox.showerror('Trusted models only', 'Select the trust checkbox only for a model you created or trust.', parent=self.window);return
        path = filedialog.askopenfilename(parent=self.window, filetypes=[('RedScrap model', '*.rsmodel')])
        if path:self.run_job('Loading model...', lambda:load_bundle(path), self.set_bundle)

    def predict(self):
        if not self.require_input():return
        if self.bundle is None:messagebox.showerror('Model required', 'Train or load a model first.', parent=self.window);return
        output = filedialog.asksaveasfilename(parent=self.window, initialfile='Comments_classified.xlsx', defaultextension='.xlsx', filetypes=[('Excel', '*.xlsx')])
        if not output:return
        if Path(output).resolve() == Path(self.input_path).resolve():
            messagebox.showerror('Choose a new file', 'Predictions must not overwrite the source dataset.', parent=self.window);return
        source, col, bundle = self.input_path, self.column.get().strip(), self.bundle
        def work():
            out, summary = predict_comments(bundle, read_data(source), col)
            write_excel(out, output)
            write_report(bundle, summary, str(Path(output).with_suffix('.pdf')))
            Path(output+'.summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
            return summary
        self.run_job('Classifying and exporting Excel, PDF and summary...', work, lambda s:self.show(json.dumps(s, indent=2)))

    def use_supplied(self):
        self.on_select(None)
        self.status.configure(text='Supplied binary model selected for subsequent Early Reports.')

    def use_model(self):
        if self.bundle is None:messagebox.showerror('Model required', 'Train or load a model first.', parent=self.window);return
        self.on_select(self.bundle)
        self.status.configure(text='Model selected for subsequent Early Reports. Topic: '+self.bundle['metadata']['topic'])


def open_workspace(parent=None, on_select=None):
    return SentimentWorkspace(parent, on_select)


if __name__ == '__main__':
    workspace = open_workspace()
    workspace.window.mainloop()
