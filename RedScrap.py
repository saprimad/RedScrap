"""RedScrap v21.9.0.

A desktop research tool for retrieving Reddit threads and comments through
PRAW, exporting structured data, and producing an exploratory PDF report.

Optional sentiment analysis uses ``sentiment_vectorizer.pkl`` and
``sentiment_model.pkl``. Place both files in the same directory as this script.
If either file is unavailable, sentiment analysis is skipped while the other
collection and reporting functions remain available.

Usage:
    python redscrap_v21.9.0.py
"""

# --- Changelog for patched version ---
# - Clean general-adaptive word frequency update: improved cleaning, combined English/Malay stopwords, and bigram support for more meaningful top-term extraction.
# - Section 8: Full Thread List now highlights zero-comment threads by rendering their titles in red, with an explanatory note.
# - Added splitByRow=True to large tables for automatic page splitting.
# - Enabled allowSplitting=True in SimpleDocTemplate to permit splitting of flowables.
# - Fixed ReportLab “Flowable too large” error.
# - Added helper functions to escape dynamic text and truncate very long strings before
#   building Paragraphs, preventing paraparser unclosed tag errors.
# - Introduced make_paragraph() and html_escape() to wrap user‑supplied text safely.
# ---

import os
import textwrap  # for safely truncating long titles and comments
import json
import time
from datetime import datetime
from collections import Counter, defaultdict
"""
This module attempts to import tkinter for GUI functionality. If tkinter
is unavailable (for example on a headless server where the Tk libraries
are not installed), the GUI features will be disabled and the script
will fall back to console-based input for credentials. This allows the
script to be executed in a wider range of environments without
immediately crashing due to a missing dependency.
"""
# Attempt to import tkinter for GUI functionality. On headless systems where
# tkinter cannot be initialized, fall back to console mode and disable GUI.
try:
    import tkinter as tk  # noqa: F401
    from tkinter import filedialog, Listbox, Scrollbar, Label, messagebox  # noqa: F401
    # Mark that Tkinter is available
    HAS_TK = True
    # Attempt to import ttk for progress bar support
    try:
        from tkinter import ttk  # type: ignore
    except Exception:
        ttk = None
except Exception:
    # If tkinter is not available or fails to initialize (e.g. no $DISPLAY)
    tk = None  # type: ignore
    HAS_TK = False
    ttk = None
    print(
        "Warning: tkinter is not available. GUI functionality will be disabled.\n"
        "You can still run the script in console mode and provide your Reddit "
        "credentials via prompts."
    )

# threading is used to run long tasks without blocking the GUI
import threading

# Conditional imports for NLP (Uncomment for actual model loading)
import joblib


try:
    import praw  # type: ignore
except ImportError as e:
    raise ImportError(
        "The 'praw' package is required to run this script but is not installed. "
        "Please install it using 'pip install praw' and try again."
    ) from e
import numpy as np
import pandas as pd
import matplotlib
# Use Agg backend for headless environments
matplotlib.use("Agg") # must set backend before importing pyplot
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.stats import skew, kurtosis
import textwrap

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
    
    )
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie # NEW: For Sentiment Pie Chart
from reportlab.lib.styles import ParagraphStyle
from xml.sax.saxutils import escape as _xml_escape  # for safe HTML escaping

__version__ = "21.9.0"

# ------------------------------------------------------------------
# Helper functions to escape dynamic text and build safe Paragraphs
# These functions avoid ReportLab 'paraparser' errors by escaping
# user‑provided strings (titles, comments, authors) and truncating
# very long content to a reasonable length. They also allow optional
# colour specification for highlighting (e.g. zero‑comment thread titles).
def _clean_ws(s: str) -> str:
    """Collapse newlines and excess whitespace, replacing non‑breaking spaces."""
    return " ".join((s or "").replace("\u00a0", " ").split())


def html_escape(s: str) -> str:
    """Escape characters that ReportLab would treat as HTML tags.

    Use xml.sax.saxutils.escape to replace & < > and also escape quotes
    to prevent malformed font tags.
    """
    return _xml_escape(_clean_ws(s), {'"': '&quot;', "'": '&#39;'})


def make_paragraph(text: str, style, color: str | None = None, max_chars: int = 2000):
    """Create a safe ReportLab Paragraph from user text.

    - Escapes HTML special characters to avoid paraparser errors.
    - Truncates extremely long cells to max_chars characters and adds ellipsis.
    - Optionally wraps the string in a <font color="…"> tag to apply colour.
    """
    esc = html_escape(text)
    if len(esc) > max_chars:
        esc = esc[: max_chars - 1] + "…"
    if color:
        esc = f'<font color="{color}">{esc}</font>'
    return Paragraph(esc, style)


# =====================================================
# Configuration and login
# =====================================================

CONFIG_FILE = "reddit_config.json"

def get_reddit():
    """Prompt the user for Reddit API credentials if not already stored.

    Returns a praw.Reddit instance configured with the user's credentials.
    """
    # First check whether a config file already exists. If so, load it.
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            cfg = json.load(f)
    else:
        # If tkinter is available, use a GUI dialog; otherwise fall back to console prompts.
        creds = {}
        if HAS_TK and tk is not None:
            # Prompt user for credentials via a simple Tkinter dialog
            try:
                login = tk.Tk()
            except Exception:
                # Could not create a Tk root (likely due to missing display)
                print(
                    "tkinter is installed but a display could not be initialized. "
                    "Falling back to console input for credentials."
                )
                cid = input("Enter your Reddit Client ID: ").strip()
                csec = input("Enter your Reddit Client Secret: ").strip()
                user_agent = input("Enter a user agent (default: 'RedScrap v21.9.0'): ").strip() or "RedScrap v21.9.0"
                if not cid or not csec:
                    raise RuntimeError(
                        "Reddit credentials are required. Please provide both client_id and client_secret."
                    )
                creds["client_id"] = cid
                creds["client_secret"] = csec
                creds["user_agent"] = user_agent
                with open(CONFIG_FILE, "w") as f:
                    json.dump(creds, f)
            else:
                login.title("RedScrap Login")
                login.resizable(False, False)
                tk.Label(login, text="Enter your Reddit API credentials", font=("Arial", 12, "bold"), pady=5).pack()
                tk.Label(login, text="Client ID:").pack()
                cid_entry = tk.Entry(login, width=40)
                cid_entry.pack(padx=10, pady=2)
                tk.Label(login, text="Client Secret:").pack()
                csec_entry = tk.Entry(login, width=40, show="*")
                csec_entry.pack(padx=10, pady=2)

                def save_and_continue():
                    cid_val = cid_entry.get().strip()
                    csec_val = csec_entry.get().strip()
                    if not cid_val or not csec_val:
                        messagebox.showerror("Error", "Please provide both Client ID and Client Secret")
                        return
                    creds["client_id"] = cid_val
                    creds["client_secret"] = csec_val
                    creds["user_agent"] = "RedScrap v21.9.0"
                    with open(CONFIG_FILE, "w") as f:
                        json.dump(creds, f)
                    login.destroy()

                tk.Button(
                    login,
                    text="Save & Continue",
                    command=save_and_continue,
                    bg="#4CAF50",
                    fg="white",
                    padx=10,
                    pady=5,
                ).pack(pady=10)
                login.mainloop()
        else:
            # Console-based input: useful on headless servers where tkinter isn't available.
            print("tkinter is not available; please enter your Reddit API credentials in the console.")
            cid = input("Enter your Reddit Client ID: ").strip()
            csec = input("Enter your Reddit Client Secret: ").strip()
            user_agent = input("Enter a user agent (default: 'RedScrap v21.9.0'): ").strip() or "RedScrap v21.9.0"
            if not cid or not csec:
                raise RuntimeError(
                    "Reddit credentials are required. Please provide both client_id and client_secret."
                )
            creds["client_id"] = cid
            creds["client_secret"] = csec
            creds["user_agent"] = user_agent
            with open(CONFIG_FILE, "w") as f:
                json.dump(creds, f)
        cfg = creds
    # When constructing the Reddit instance, it's useful to disable async checks to avoid warnings.
    return praw.Reddit(
        client_id=cfg["client_id"],
        client_secret=cfg["client_secret"],
        user_agent=cfg.get("user_agent", "RedScrap v21.9.0"),
        # The following kwargs avoid PRAW complaining about async loops when running inside certain environments.
        check_for_async=False,
    )


# =====================================================
# Scraper
# =====================================================

class Scraper:
    """Fetch threads and comments from Reddit using PRAW."""

    def __init__(self, reddit, subreddit, keywords, start_date, end_date):
        self.reddit = reddit
        self.subreddit = subreddit
        # Ensure multi-word keywords are wrapped in quotes for exact match
        self.keywords = [f'"{k.strip()}"' if " " in k else k.strip() for k in keywords]
        self.start_date = start_date
        self.end_date = end_date
        self.posts = []

    def fetch_threads(self, limit=200):
        """Search for threads matching the keywords between start_date and end_date."""
        query = " OR ".join(self.keywords) if self.keywords else "*"
        results = []
        # Convert dates to UNIX timestamps
        try:
            start_ts = int(time.mktime(datetime.strptime(self.start_date, "%Y-%m-%d").timetuple()))
        except Exception:
            start_ts = 0
        try:
            end_ts = int(time.mktime(datetime.strptime(self.end_date, "%Y-%m-%d").timetuple()))
        except Exception:
            end_ts = int(time.time())
        for submission in self.reddit.subreddit(self.subreddit).search(query, sort="new", limit=limit):
            created = int(submission.created_utc)
            if start_ts <= created <= end_ts:
                results.append(submission)
        self.posts = results
        return results


# =====================================================
# Analyzer v2 (with Sentiment Analysis)
# =====================================================

class Analyzer:
    """Perform analyses on scraped data: descriptive stats, frequency, temporal patterns, etc."""

    def __init__(self, posts):
        self.posts = posts or []
        # Gather comments from posts into a DataFrame
        self.comments = self._collect_comments()
        
        # --- NEW: Perform Sentiment Analysis on initialization ---
        self.sentiment_model_loaded = self.load_sentiment_model()
        if self.sentiment_model_loaded:
            self.perform_sentiment_analysis()
        else:
            # Add a placeholder column even if the model isn't loaded
            self.comments["sentiment"] = None 
        # --------------------------------------------------------

    def _collect_comments(self):
        """Collect comments into a pandas DataFrame with fields: author, body, upvotes, created (datetime)."""
        data = []
        for sub in self.posts:
            try:
                sub.comments.replace_more(limit=None)
            except Exception:
                continue
            for c in sub.comments.list():
                data.append({
                    "author": str(c.author),
                    "body": c.body if c.body is not None else "",
                    "upvotes": c.score,
                    "created": datetime.utcfromtimestamp(getattr(c, 'created_utc', time.time()))
                })
        if not data:
            # return empty DataFrame with necessary columns
            return pd.DataFrame(columns=["author", "body", "upvotes", "created"])
        return pd.DataFrame(data)

    # Descriptive stats for upvotes
    def descriptive_stats_upvotes(self):
        data = self.comments["upvotes"].dropna().astype(float)
        if len(data) == 0:
            return {}
        stats = {
            "n": int(len(data)),
            "mean": float(np.mean(data)),
            "median": float(np.median(data)),
            "mode": float(data.mode().iloc[0]) if not data.mode().empty else 0.0,
            "min": float(np.min(data)),
            "max": float(np.max(data)),
            "range": float(np.max(data) - np.min(data)),
            "std": float(np.std(data)),
            "var": float(np.var(data)),
            "p25": float(np.percentile(data, 25)),
            "p50": float(np.percentile(data, 50)),
            "p75": float(np.percentile(data, 75)),
            "p95": float(np.percentile(data, 95)),
            "skew": float(skew(data)),
            "kurtosis": float(kurtosis(data)),
        }
        return stats

    # Descriptive stats for comment length
    def descriptive_stats_comment_length(self):
        lengths = self.comments["body"].dropna().apply(lambda x: len(str(x)))
        if len(lengths) == 0:
            return {}
        data = lengths.astype(float)
        stats = {
            "n": int(len(data)),
            "mean": float(np.mean(data)),
            "median": float(np.median(data)),
            "mode": float(data.mode().iloc[0]) if not data.mode().empty else 0.0,
            "min": float(np.min(data)),
            "max": float(np.max(data)),
            "range": float(np.max(data) - np.min(data)),
            "std": float(np.std(data)),
            "var": float(np.var(data)),
            "p25": float(np.percentile(data, 25)),
            "p50": float(np.percentile(data, 50)),
            "p75": float(np.percentile(data, 75)),
            "p95": float(np.percentile(data, 95)),
            "skew": float(skew(data)),
            "kurtosis": float(kurtosis(data)),
        }
        return stats

    def year_summary(self):
        """Return thread and comment counts by year."""
        thread_counts = Counter()
        comment_counts = Counter()
        # Threads
        for sub in self.posts:
            yr = datetime.utcfromtimestamp(getattr(sub, 'created_utc', time.time())).year
            thread_counts[yr] += 1
        # Comments
        for dt in self.comments["created"]:
            comment_counts[dt.year] += 1
        return thread_counts, comment_counts

    def word_frequency(self, n=20, stopwords=None):
        """Return the top ``n`` most common terms (unigrams and bigrams) in the comments.

        This implementation expands on the original by performing additional
        cleaning, leveraging a broader set of English and Malay stopwords and
        optionally generating simple bigrams.  Contraction artifacts such as
        ``"s"`` or ``"t"`` that result from apostrophe stripping are explicitly
        removed.  The method is suitable for arbitrary datasets and does not
        enforce any domain-specific filtering.

        :param n: Number of top terms to return.
        :param stopwords: Optional set of stopwords to exclude.  If none is
            provided, a combined English/Malay set with additional contraction
            tokens will be used.
        :returns: List of (term, count) tuples sorted by descending frequency.
        """
        import re
        # Define a comprehensive set of default stopwords if none provided.
        if stopwords is None:
            english_stop = {
                "the","and","a","to","of","in","is","it","that","for","on","with","as",
                "this","i","you","are","be","or","was","by","an","at","from","not",
                "we","they","have","has","had","he","she","his","her","their","them","its",
                "so","if","but","my","me","our","your","us","will","just","more","do","does",
                "did","should","could","would","may","might","also","u","im","one","two","three",
                "can","cant","cannot"
            }
            # Common Malay stopwords (not exhaustive but captures frequent function words)
            malay_stop = {
                "yang","dan","dengan","untuk","pada","adalah","ini","itu","saya","kami",
                "kamu","dia","mereka","kita","dari","ke","tidak","akan","juga","oleh",
                "agar","dapat","atau","kerana","serta","ia","sebagai","dalam","lebih",
                "per","ber","ter","ma","se","kau","aku","tak","lah","mcm","yg"
            }
            # Additional tokens resulting from contractions or common noise
            contraction_tokens = {
                "s","t","m","re","ve","ll","don","d","amp","ampamp","http","https",
                "deleted","removed","edit"
            }
            stopwords = english_stop | malay_stop | contraction_tokens
        # Concatenate all comment bodies into a single string
        text = " ".join(self.comments["body"].dropna().astype(str))
        # Remove URLs completely
        text = re.sub(r"http\S+", " ", text)
        # Normalize to lowercase and replace non-alphanumeric characters with spaces
        cleaned = ''.join(ch.lower() if ch.isalnum() or ch.isspace() else ' ' for ch in text)
        tokens = cleaned.split()
        # Filter tokens: remove stopwords, numeric strings, and very short tokens
        filtered = [w for w in tokens if w not in stopwords and not w.isdigit() and len(w) > 2]
        # Count unigrams
        freq = Counter(filtered)
        # Generate simple bigrams (adjacent token pairs) and accumulate counts
        bigrams = []
        for i in range(len(filtered) - 1):
            w1, w2 = filtered[i], filtered[i+1]
            # Skip bigrams with identical tokens
            if w1 != w2:
                bigrams.append(f"{w1} {w2}")
        bigram_freq = Counter(bigrams)
        # Combine unigram and bigram counts
        combined = freq + bigram_freq
        # Return the top n terms by frequency
        return combined.most_common(n)

    def temporal_summary(self):
        """Compute daily and hourly comment counts and identify peak day and hour."""
        if self.comments.empty:
            return (pd.Series(dtype=int), pd.Series(dtype=int), None, None)
        df = self.comments.copy()
        df["date"] = df["created"].dt.date
        df["hour"] = df["created"].dt.hour
        daily = df.groupby("date").size().sort_index()
        hourly = df.groupby("hour").size().sort_index()
        peak_day = None
        peak_hour = None
        if not daily.empty:
            peak_day = daily.idxmax()
        if not hourly.empty:
            peak_hour = int(hourly.idxmax())
        return daily, hourly, peak_day, peak_hour

    def engagement_summary(self):
        """Return summary of engagement and missingness (deleted/removed comments, zero-comment threads)."""
        zero_comment_threads = sum(1 for sub in self.posts if getattr(sub, 'num_comments', 0) == 0)
        deleted_or_removed = self.comments["body"].apply(lambda b: b in ("", "[deleted]", "[removed]"))
        deleted_count = int(deleted_or_removed.sum())
        active_count = len(self.comments) - deleted_count
        ratio_active_deleted = (active_count / deleted_count) if deleted_count else None
        return {
            "zero_comment_threads": zero_comment_threads,
            "deleted_comments": deleted_count,
            "active_comments": active_count,
            "active_vs_deleted_ratio": ratio_active_deleted,
        }

    def top_threads_by_comments(self, n=20):
        """Return a list of the top n threads by comment count."""
        sorted_posts = sorted(
            self.posts,
            key=lambda s: getattr(s, 'num_comments', 0),
            reverse=True
        )
        return sorted_posts[:n]

    def top_comments_by_upvotes(self, n=20):
        """Return a DataFrame of the top n comments by upvotes."""
        if self.comments.empty:
            return pd.DataFrame(columns=self.comments.columns)
        df = self.comments.sort_values(by="upvotes", ascending=False).head(n)
        return df

    # =======================================================
    # NEW: SENTIMENT ANALYSIS METHODS
    # =======================================================

    def load_sentiment_model(self):
        """Load the pre-trained vectorizer and classifier from .pkl files."""
        try:
            if os.path.exists("sentiment_vectorizer.pkl") and os.path.exists("sentiment_model.pkl"):
                print("Sentiment model files found. Loading trained TF-IDF vectorizer and classifier.")
                self.vectorizer = joblib.load("sentiment_vectorizer.pkl")
                self.model = joblib.load("sentiment_model.pkl")
                return True
            else:
                print("Sentiment model files (sentiment_vectorizer.pkl, sentiment_model.pkl) not found. Skipping sentiment analysis.")
                return False
        except Exception as e:
            print(f"Error loading sentiment model: {e}. Skipping analysis.")
            return False

    def perform_sentiment_analysis(self):
        """Analyze the sentiment of all comments and add a 'sentiment' column."""
        if not self.sentiment_model_loaded:
            self.comments["sentiment"] = None
            return

        comment_bodies = self.comments["body"].dropna().astype(str)
        if comment_bodies.empty:
            self.comments["sentiment"] = None
            return
            
        # Transform comments using the fitted TF-IDF vectorizer and classify
        # them with the trained binary sentiment model.
        X = self.vectorizer.transform(comment_bodies)
        predictions = self.model.predict(X)

        # Preserve string labels when the classifier already emits them; otherwise
        # map conventional binary labels (0/1) to Negative/Positive.
        pred_series = pd.Series(predictions, index=comment_bodies.index)
        if set(pred_series.dropna().unique()).issubset({0, 1}):
            sentiment_series = pred_series.map({0: "Negative", 1: "Positive"})
        else:
            sentiment_series = pred_series.astype(str)
        
        # Merge the new sentiment data back into the main DataFrame
        self.comments["sentiment"] = sentiment_series


    def sentiment_summary(self):
        """Return the count and percentage of each sentiment category."""
        if not self.sentiment_model_loaded or self.comments["sentiment"].isnull().all():
            return {}

        summary = self.comments["sentiment"].value_counts().to_dict()
        total = sum(summary.values())
        if total == 0:
            return {}
            
        # Calculate percentages
        percentages = {k: v / total * 100 for k, v in summary.items()}
        
        return {"counts": summary, "percentages": percentages}


# =====================================================
# Exporter
# =====================================================

class Exporter:
    @staticmethod
    def generate_pdf_enhanced(posts, analyzer, filename, meta):
        """Generate a multi-page PDF report with enhanced analyses."""
        # Set up document
        doc = SimpleDocTemplate(
            filename,
            pagesize=landscape(letter),
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
            allowSplitting=True,
        )
        styles = getSampleStyleSheet()
        # Create a body style that forcibly wraps long words to avoid oversized table rows.
        # Using wordWrap='CJK' allows the paragraph to break long words at character boundaries,
        # ensuring that extremely long titles or comments (e.g., long URLs or unbroken strings)
        # do not cause a single table row to exceed the available page height.
        body_wrap_style = ParagraphStyle(name='BodyWrap', parent=styles.get('BodyText', styles['Normal']), wordWrap='CJK')
        # Define custom styles for captions, notes, and centered titles
        caption_style = ParagraphStyle(
            name='Caption',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,  # center alignment
            spaceBefore=4,
            spaceAfter=4
        )
        note_style = ParagraphStyle(
            name='Note',
            parent=styles['Normal'],
            fontSize=8,
            italic=True,
            alignment=1,
            spaceBefore=4,
            spaceAfter=4
        )
        title_style = ParagraphStyle(
            name='TitleCenter',
            parent=styles['Title'],
            alignment=1  # center title
        )
        story = []

        # Unpack metadata
        subreddit = meta.get("subreddit", "N/A")
        keywords = meta.get("keywords", [])
        keywords_str = ", ".join(keywords) if keywords else "All"
        start_date = meta.get("start_date", "N/A")
        end_date = meta.get("end_date", "N/A")
        generated_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # -------------------------------------------------
        # Page 1: Executive summary
        # -------------------------------------------------
        title = "RedScrap Early Report"
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))
        meta_text = (
            f"Subreddit: r/{subreddit}<br/>"
            f"Keywords: {keywords_str}<br/>"
            f"Date Range: {start_date} to {end_date}<br/>"
            f"Report Generated: {generated_on}"\
        )
        story.append(Paragraph(meta_text, styles["Normal"]))
        story.append(Spacer(1, 12))

        # Section 1 heading: Metadata overview
        story.append(Paragraph("Section 1. Metadata Overview", styles["Heading1"]))

        # Summary counts
        n_threads = len(posts)
        n_comments = len(analyzer.comments)
        total_upvotes = int(analyzer.comments["upvotes"].sum()) if not analyzer.comments.empty else 0
        avg_comments_per_thread = round(n_comments / n_threads, 2) if n_threads else 0

        summary_data = [
            ["Metric", "Value"],
            ["Total Threads", n_threads],
            ["Total Comments", n_comments],
            ["Average Comments per Thread", avg_comments_per_thread],
            ["Total Upvotes", total_upvotes],
        ]
        summary_table = Table(summary_data, colWidths=[200, 200])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))
        summary_table.hAlign = 'CENTER'
        story.append(summary_table)
        # Caption for Table 1: dataset metadata summary
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            "Table 1. Dataset metadata summary (threads, comments, time span).",
            caption_style
        ))
        story.append(PageBreak())

        # -------------------------------------------------
        # Page 2: Section 2 – Descriptive statistics for upvotes & comment length
        # -------------------------------------------------
        story.append(Paragraph("Section 2. Descriptive Statistics", styles["Heading1"]))
        stats_upvotes = analyzer.descriptive_stats_upvotes()
        stats_length = analyzer.descriptive_stats_comment_length()
        if stats_upvotes and stats_length:
            # Prepare combined table: metric, upvotes value, comment length value
            headers = ["Metric", "Upvotes", "Comment Length"]
            rows = []
            # Use same order for both stats
            metrics_order = [
                "n", "mean", "median", "mode", "min", "max", "range", 
                "std", "var", "p25", "p50", "p75", "p95", "skew", "kurtosis"
            ]
            for m in metrics_order:
                up_val = stats_upvotes.get(m, '')
                len_val = stats_length.get(m, '')
                # Round floats to 2 decimals for readability
                def fmt(x):
                    return f"{x:.2f}" if isinstance(x, float) else x

                rows.append([m.capitalize(), fmt(up_val), fmt(len_val)])
            desc_data = [headers] + rows
            desc_table = Table(desc_data, colWidths=[150, 175, 175])
            desc_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]))
            # Center the descriptive statistics table
            desc_table.hAlign = 'CENTER'
            story.append(desc_table)
            # Caption for Table 2
            story.append(Spacer(1, 6))
            story.append(Paragraph(
                "Table 2. Descriptive statistics of upvotes and comment length.",
                caption_style
            ))
            # -----------------------------------------------------------------
            # Provide narrative explanations for each descriptive statistic
            # -----------------------------------------------------------------
            def generate_description(name: str, stats: dict) -> str:
                """Create a human‑readable explanation of descriptive stats for a given metric."""
                n = stats.get('n', 0)
                mean = stats.get('mean', 0)
                median = stats.get('median', 0)
                mode = stats.get('mode', 0)
                minv = stats.get('min', 0)
                maxv = stats.get('max', 0)
                rng = stats.get('range', 0)
                std = stats.get('std', 0)
                var = stats.get('var', 0)
                p25 = stats.get('p25', 0)
                p50 = stats.get('p50', 0)
                p75 = stats.get('p75', 0)
                p95 = stats.get('p95', 0)
                skew = stats.get('skew', 0)
                kurt = stats.get('kurtosis', 0)
                # Interpret skewness
                if skew > 0:
                    skew_desc = "right-skewed (a longer tail towards larger values)"
                elif skew < 0:
                    skew_desc = "left-skewed (a longer tail towards smaller values)"
                else:
                    skew_desc = "approximately symmetric"
                # Interpret kurtosis
                if kurt > 0:
                    kurt_desc = "heavy-tailed and peaked compared to a normal distribution"
                elif kurt < 0:
                    kurt_desc = "light-tailed and flatter than a normal distribution"
                else:
                    kurt_desc = "similar to a normal distribution"
                explanation = (
                    f"For {name}, {n} values were analyzed. The mean {name} is {mean:.2f}, which is the average value. "
                    f"The median ({p50:.2f}) indicates that half of the values are below this number, while the mode ({mode:.2f}) represents the most common value. "
                    f"The minimum ({minv:.2f}) and maximum ({maxv:.2f}) give a range of {rng:.2f}. "
                    f"The standard deviation ({std:.2f}) and variance ({var:.2f}) measure how spread out the values are around the mean. "
                    f"The 25th percentile (p25 = {p25:.2f}), 50th percentile (p50 = {p50:.2f}), 75th percentile (p75 = {p75:.2f}), and 95th percentile (p95 = {p95:.2f}) show how the data is distributed across the spectrum of values. "
                    f"A skewness of {skew:.2f} indicates that the distribution is {skew_desc}. "
                    f"The kurtosis of {kurt:.2f} suggests that the distribution is {kurt_desc}."
                )
                return explanation
            # Create and append explanation paragraphs for upvotes and comment length
            expl_upvotes = generate_description("upvotes", stats_upvotes)
            expl_length = generate_description("comment length", stats_length)
            story.append(Spacer(1, 12))
            story.append(Paragraph(expl_upvotes, styles["Normal"]))
            story.append(Spacer(1, 6))
            story.append(Paragraph(expl_length, styles["Normal"]))
        else:
            story.append(Paragraph("No descriptive statistics available (no comments collected).", styles["Normal"]))
        story.append(PageBreak())

        # -------------------------------------------------
        # Page 3: Section 3 – Post Type Summary
        # -------------------------------------------------
        story.append(Paragraph('Section 3. Post Type Summary', styles['Heading1']))
        # Compute post type counts across threads
        categories = ['Text', 'Image', 'Video', 'Poll', 'Link', 'Other']
        pt_counts = {cat: 0 for cat in categories}
        for sub in posts:
            try:
                if getattr(sub, 'poll_data', None) is not None:
                    pt_counts['Poll'] += 1
                elif getattr(sub, 'is_self', False):
                    pt_counts['Text'] += 1
                else:
                    hint = getattr(sub, 'post_hint', None)
                    url_l = getattr(sub, 'url', '').lower()
                    if hint == 'image' or url_l.endswith(('.jpg', '.png', '.gif')):
                        pt_counts['Image'] += 1
                    elif hint in ('hosted:video', 'rich:video'):
                        pt_counts['Video'] += 1
                    elif hint == 'link':
                        pt_counts['Link'] += 1
                    else:
                        pt_counts['Other'] += 1
            except Exception:
                pt_counts['Other'] += 1
        # Calculate percentages
        pt_total = len(posts) if len(posts) > 0 else sum(pt_counts.values())
        pt_percent = {k: (pt_counts[k] / pt_total * 100 if pt_total else 0) for k in categories}
        # Build table data
        pt_table_data = [['Post Type', 'Count', 'Percentage (%)']]
        for cat in categories:
            pt_table_data.append([cat, pt_counts[cat], f"{pt_percent[cat]:.2f}%"])
        pt_table = Table(pt_table_data, colWidths=[150, 150, 150])
        pt_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))
        # Center the post type table
        pt_table.hAlign = 'CENTER'
        story.append(pt_table)
        # Caption for Table 3
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            'Table 3. Distribution of post types by count and percentage.',
            caption_style
        ))
        story.append(Spacer(1, 24))
        # Pie chart for post types
        pt_drawing = Drawing(500, 250)
        pt_pie = Pie()
        pt_pie.x = 100
        pt_pie.y = 50
        pt_pie.width = 150
        pt_pie.height = 150
        pt_pie.data = [pt_counts[cat] for cat in categories]
        pt_pie.labels = [f"{cat} ({pt_percent[cat]:.1f}%)" for cat in categories]
        pt_pie.slices.strokeWidth = 0.5
        # Assign colours for each post type
        type_colours = {
            'Text': colors.blue,
            'Image': colors.orange,
            'Video': colors.green,
            'Poll': colors.purple,
            'Link': colors.brown,
            'Other': colors.gray,
        }
        for idx, cat in enumerate(categories):
            pt_pie.slices[idx].fillColor = type_colours.get(cat, colors.gray)
        pt_drawing.add(pt_pie)
        # Center the drawing
        pt_drawing.hAlign = 'CENTER'
        story.append(pt_drawing)
        # Caption for Figure 1
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            'Figure 1. Distribution of post types in the dataset.',
            caption_style
        ))
        # Note about post type classification
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            '<i>Note: Post type classification is based on Reddit metadata</i>',
            note_style
        ))
        story.append(PageBreak())

        # -------------------------------------------------
        # Page 4: Section 4 – Sentiment Analysis Summary
        # -------------------------------------------------
        story.append(Paragraph('Section 4. Sentiment Analysis Summary', styles['Heading1']))
        sentiment_data = analyzer.sentiment_summary()

        if sentiment_data:
            counts = sentiment_data['counts']
            percentages = sentiment_data['percentages']

            # 1. Summary Table
            sent_table_data = [["Sentiment", "Count", "Percentage (%)"]]
            # Sort keys to ensure 'Negative' and 'Positive' are handled consistently for the pie chart colors
            sorted_sentiments = sorted(counts.keys(), reverse=True) # Assuming 'Positive' comes before 'Negative' to match color scheme
            
            sent_table_data.extend([
                [s, counts.get(s, 0), f"{percentages.get(s, 0):.2f}%"] for s in sorted_sentiments
            ])
            
            sent_table = Table(sent_table_data, colWidths=[150, 150, 150])
            sent_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]))
            # Center the sentiment table
            sent_table.hAlign = 'CENTER'
            story.append(sent_table)
            # Caption for Table 4
            story.append(Spacer(1, 6))
            story.append(Paragraph(
                "Table 4. Sentiment distribution (positive vs negative).",
                caption_style
            ))
            # Provide a bit more space before the pie chart
            story.append(Spacer(1, 18))

            # 2. Pie Chart
            pie_drawing = Drawing(500, 250)
            pie = Pie()
            pie.x = 100
            pie.y = 50
            pie.width = 150
            pie.height = 150
            
            # Prepare data and labels for ReportLab Pie Chart
            data = [counts.get(s, 0) for s in sorted_sentiments]
            labels = [f"{s} ({percentages.get(s, 0):.1f}%)" for s in sorted_sentiments]
            
            pie.data = data
            pie.labels = labels
            pie.slices.strokeWidth = 0.5
            
            # Assign colors based on sorted keys
            sentiment_colors = {
                'Positive': colors.green,
                'Negative': colors.red,
                # Add 'Neutral' if you upgrade to a ternary model
            }
            for i, sentiment in enumerate(sorted_sentiments):
                if i < len(pie.data):
                    pie.slices[i].fillColor = sentiment_colors.get(sentiment, colors.gray)

            pie_drawing.add(pie)
            # Center the sentiment pie chart drawing
            pie_drawing.hAlign = 'CENTER'
            story.append(pie_drawing)
            # Caption for Figure 2
            story.append(Spacer(1, 6))
            story.append(Paragraph(
                "Figure 2. Sentiment distribution pie chart.",
                caption_style
            ))

            # 3. Narrative explanation of sentiment results
            total_comments = sum(counts.get(s, 0) for s in counts)
            pos_count = counts.get('Positive', 0)
            neg_count = counts.get('Negative', 0)
            if total_comments > 0:
                pos_pct = percentages.get('Positive', 0)
                neg_pct = percentages.get('Negative', 0)
                explanation = (
                    f"Out of {total_comments} comments analyzed, "
                    f"{pos_count} ({pos_pct:.1f}%) were classified as Positive and "
                    f"{neg_count} ({neg_pct:.1f}%) were classified as Negative. "
                )
                # Determine leaning
                if abs(pos_pct - neg_pct) < 5:
                    explanation += "This indicates a relatively balanced sentiment, showing both support and opposition are present."
                elif pos_pct > neg_pct:
                    explanation += "Overall sentiment leans positive."
                else:
                    explanation += "Overall sentiment leans negative."
                story.append(Spacer(1, 12))
                story.append(Paragraph(explanation, styles["Normal"]))

            # 4. Note about Sentiment140 limitations
            note_text = (
                "<i>Note: Sentiment classification was performed using the Sentiment140 dataset "
                "(binary: positive/negative). Although validated in its original Twitter context, "
                "its accuracy for Reddit data may be limited.</i>"
            )
            story.append(Spacer(1, 6))
            story.append(Paragraph(note_text, note_style))
            
        else:
            story.append(Paragraph("Sentiment analysis skipped. Model files (sentiment_vectorizer.pkl, sentiment_model.pkl) not found, or no comments collected.", styles["Normal"]))
            
        story.append(PageBreak())
        # -------------------------------------------------


        # -------------------------------------------------
        # Page 4 (Original Page 3): Yearly breakdown
        # -------------------------------------------------
        story.append(Paragraph("Section 5. Threads and Comments by Year", styles["Heading1"]))
        threads_year, comments_year = analyzer.year_summary()
        years = sorted(set(list(threads_year.keys()) + list(comments_year.keys())))
        year_table_data = [["Year", "Threads", "Comments"]]
        for yr in years:
            year_table_data.append([str(yr), threads_year.get(yr, 0), comments_year.get(yr, 0)])
        year_table = Table(year_table_data, colWidths=[100, 150, 150])
        year_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))
        # Center the year table
        year_table.hAlign = 'CENTER'
        story.append(year_table)
        # Caption for Table 5 (threads and comments by year)
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            "Table 5. Threads and comments by year.",
            caption_style
        ))
        story.append(Spacer(1, 12))

        # Bar chart using reportlab VerticalBarChart
        if years:
            bar_drawing = Drawing(500, 250)
            chart = VerticalBarChart()
            chart.x = 50
            chart.y = 40
            chart.height = 200
            chart.width = 400
            chart.data = [
                [threads_year.get(yr, 0) for yr in years],
                [comments_year.get(yr, 0) for yr in years],
            ]
            chart.categoryAxis.categoryNames = [str(yr) for yr in years]
            chart.valueAxis.valueMin = 0
            chart.valueAxis.valueMax = max(max(chart.data[0]), max(chart.data[1])) * 1.1 if years else 1
            chart.valueAxis.valueStep = max(1, int(chart.valueAxis.valueMax / 10))
            chart.barLabels.nudge = 7
            chart.barLabelFormat = '%d'
            bar_drawing.add(chart)
            # Center the bar chart drawing
            bar_drawing.hAlign = 'CENTER'
            story.append(bar_drawing)
            # Caption for Figure 3
            story.append(Spacer(1, 6))
            story.append(Paragraph(
                "Figure 3. Number of threads and comments by year.",
                caption_style
            ))
        else:
            story.append(Paragraph("No year information available.", styles["Normal"]))
        story.append(PageBreak())

        # -------------------------------------------------
        # Page 6: Section 6 – Word Frequency and Visualization
        # -------------------------------------------------
        story.append(Paragraph("Section 6. Word Frequency and Visualization", styles["Heading1"]))
        freq_list = analyzer.word_frequency(n=20)
        if freq_list:
            # Build table of words and counts
            word_table_data = [["Word", "Count"]] + [[w, c] for w, c in freq_list]
            word_table = Table(word_table_data, colWidths=[200, 100])
            word_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]))
            story.append(word_table)
            # Caption for Table 5
            story.append(Spacer(1, 6))
            story.append(Paragraph(
                "Table 6. Top keywords by frequency.",
                caption_style
            ))
            story.append(Spacer(1, 12))
            # Create bar chart using matplotlib
            words = [w for w, c in freq_list]
            counts = [c for w, c in freq_list]
            plt.figure(figsize=(8, 4))
            plt.bar(range(len(words)), counts)
            plt.xticks(range(len(words)), words, rotation=45, ha='right')
            plt.title('Top 20 Word Frequencies')
            plt.tight_layout()
            freq_img_path = os.path.join(os.getcwd(), 'word_freq_bar.png')
            plt.savefig(freq_img_path)
            plt.close()
            # Embed image
            # Center the bar chart image
            img = Image(freq_img_path, width=500, height=250)
            img.hAlign = 'CENTER'
            story.append(img)
            # Caption for Figure 4 (Top 20 Word Frequency)
            story.append(Spacer(1, 6))
            story.append(Paragraph(
                "Figure 4. Top 20 Word Frequency.",
                caption_style
            ))
            # Generate temporal summary charts (peak day and hour)
            daily, hourly, peak_day, peak_hour = analyzer.temporal_summary()
            # Peak day chart
            if not daily.empty:
                fig, ax = plt.subplots(figsize=(8, 3))
                # Convert dates to strings to improve readability on x-axis
                day_labels = [str(d) for d in daily.index]
                ax.bar(day_labels, daily.values)
                ax.set_xlabel('Date')
                ax.set_ylabel('Comments')
                ax.set_title('Peak Day by Comments')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                peak_day_path = os.path.join(os.getcwd(), 'peak_day.png')
                plt.savefig(peak_day_path)
                plt.close()
                peak_day_img = Image(peak_day_path, width=500, height=250)
                peak_day_img.hAlign = 'CENTER'
                story.append(Spacer(1, 12))
                story.append(peak_day_img)
                story.append(Spacer(1, 6))
                story.append(Paragraph(
                    "Figure 5. Peak day by comments.",
                    caption_style
                ))
            # Peak hour chart
            if not hourly.empty:
                fig, ax = plt.subplots(figsize=(8, 3))
                ax.bar([str(h) for h in hourly.index], hourly.values)
                ax.set_xlabel('Hour of Day')
                ax.set_ylabel('Comments')
                ax.set_title('Peak Hour by Comments')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                peak_hour_path = os.path.join(os.getcwd(), 'peak_hour.png')
                plt.savefig(peak_hour_path)
                plt.close()
                peak_hour_img = Image(peak_hour_path, width=500, height=250)
                peak_hour_img.hAlign = 'CENTER'
                story.append(Spacer(1, 12))
                story.append(peak_hour_img)
                story.append(Spacer(1, 6))
                story.append(Paragraph(
                    "Figure 6. Peak hour by comments.",
                    caption_style
                ))
        else:
            story.append(Paragraph("No words to display.", styles["Normal"]))
        story.append(PageBreak())

        # (Removed separate Temporal Analysis section; temporal charts are integrated into Section 6)

        # -------------------------------------------------
        # Page 7: Section 7 – Top Threads and Comments
        # -------------------------------------------------
        story.append(Paragraph("Section 7. Top Threads and Comments", styles["Heading1"]))
        top_threads = analyzer.top_threads_by_comments(n=20)
        if top_threads:
            thread_table_data = [["Rank", "Title", "Comments", "Upvotes", "Date"]]
            for i, sub in enumerate(top_threads, start=1):
                # Clean and replace unsupported characters in thread title
                raw_title = " ".join(str(sub.title).split())
                def clean_text(s: str) -> str:
                    return s.replace('—','-').replace('–','-').replace('\u00a0',' ').replace('▮','-')
                cleaned_title = clean_text(raw_title)
                # Use Paragraph for automatic word wrapping within the cell
                # Use make_paragraph to escape HTML and truncate long titles
                title_para = make_paragraph(cleaned_title, body_wrap_style)
                comments_count = getattr(sub, 'num_comments', 0)
                upvotes = getattr(sub, 'score', 0)
                date_str = datetime.utcfromtimestamp(getattr(sub, 'created_utc', time.time())).strftime('%Y-%m-%d')
                thread_table_data.append([i, title_para, comments_count, upvotes, date_str])
            # Adjust column widths: more space for title, less for others
            thread_table = Table(thread_table_data, colWidths=[40, 400, 60, 60, 80], repeatRows=1, splitByRow=True)
            thread_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            # Center the table
            thread_table.hAlign = 'CENTER'
            story.append(thread_table)
            # Caption for Table 7 (Top threads by engagement)
            story.append(Spacer(1, 6))
            story.append(Paragraph(
                "Table 7. Top 20 threads by engagement.",
                caption_style
            ))
        else:
            story.append(Paragraph("No thread data available.", styles["Normal"]))
        story.append(PageBreak())

        # -------------------------------------------------
        # Page 8: Top 20 comments by upvotes
        # -------------------------------------------------
        story.append(Paragraph("Top 20 Comments (by Upvotes)", styles["Heading1"]))
        top_comments = analyzer.top_comments_by_upvotes(n=20)
        if not top_comments.empty:
            comment_table_data = [["Rank", "Author", "Comment", "Upvotes", "Date"]]
            def clean_text(s: str) -> str:
                return s.replace('—','-').replace('–','-').replace('\u00a0',' ').replace('▮','-')
            for i, row in enumerate(top_comments.itertuples(), start=1):
                # Clean comment text: remove newlines and extra spaces, replace unsupported characters
                raw_comment = " ".join(str(row.body).split())
                cleaned_comment = clean_text(raw_comment)
                # Use Paragraph for automatic word wrapping
                # Use make_paragraph for safe comment rendering
                comment_para = make_paragraph(cleaned_comment, body_wrap_style)
                # Wrap author name using make_paragraph to escape any unsafe characters
                author_para = make_paragraph(str(row.author), body_wrap_style)
                comment_table_data.append([
                    i,
                    author_para,
                    comment_para,
                    int(row.upvotes),
                    row.created.strftime('%Y-%m-%d'),
                ])
            # Adjust column widths: give more space to comment text and author
            comment_table = Table(comment_table_data, colWidths=[40, 100, 420, 60, 80], repeatRows=1, splitByRow=True)
            comment_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            # Center the table
            comment_table.hAlign = 'CENTER'
            story.append(comment_table)
            # Caption for Table 8 (Top comments by upvotes)
            story.append(Spacer(1, 6))
            story.append(Paragraph(
                "Table 8. Top 20 comments by upvotes.",
                caption_style
            ))
        else:
            story.append(Paragraph("No comment data available.", styles["Normal"]))
        story.append(PageBreak())

        # -------------------------------------------------
        # Page 9+: Section 8 – Full Thread List
        # -------------------------------------------------
        story.append(Paragraph("Section 8. Full Thread List", styles["Heading1"]))
        if posts:
            full_table_data = [["No", "Title", "Upvotes", "Comments", "Date"]]
            def clean_text(s: str) -> str:
                return s.replace('—','-').replace('–','-').replace('\u00a0',' ').replace('▮','-')
            for i, sub in enumerate(posts, start=1):
                raw_title = " ".join(str(sub.title).split())
                cleaned_title = clean_text(raw_title)
                upvotes = getattr(sub, 'score', 0)
                comments_count = getattr(sub, 'num_comments', 0)
                date_str = datetime.utcfromtimestamp(getattr(sub, 'created_utc', time.time())).strftime('%Y-%m-%d')
                # Highlight titles of threads with zero comments in red
                if comments_count == 0:
                    # Zero-comment threads: wrap title in red font via make_paragraph
                    title_para = make_paragraph(cleaned_title, body_wrap_style, color="red")
                else:
                    # Normal threads: escape HTML via make_paragraph
                    title_para = make_paragraph(cleaned_title, body_wrap_style)
                full_table_data.append([i, title_para, upvotes, comments_count, date_str])
            # Adjust column widths for full list: allocate more space for title and date
            full_table = Table(full_table_data, colWidths=[40, 400, 60, 60, 80], repeatRows=1, splitByRow=True)
            full_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            # Center the table
            full_table.hAlign = 'CENTER'
            story.append(full_table)
            # Add explanatory note indicating red titles mark zero-comment threads
            story.append(Spacer(1, 4))
            note_style = styles["Italic"] if "Italic" in styles else caption_style
            story.append(Paragraph(
                "Note: Red-colored thread titles indicate zero-comment threads.",
                note_style
            ))
            # Caption for Table 9 (complete thread list)
            story.append(Spacer(1, 6))
            story.append(Paragraph(
                "Table 9. Complete list of threads with metadata.",
                caption_style
            ))
        else:
            story.append(Paragraph("No threads found.", styles["Normal"]))
        story.append(PageBreak())

        # -------------------------------------------------
        # Final page: Citation
        # -------------------------------------------------
        citation_text = (
            "Cite this tool:<br/>"
            "Tumiran, M. S., Abd Wahab, M. S., Jamal, J. A., & Othman, N. (2026). "
            "RedScrap: Python Tool for Netnographic Data Collection (Version 21.9.0) "
            "[Computer software]. Zenodo. https://doi.org/10.5281/zenodo.22866437<br/>"
            "Corresponding author: saprimad@moh.gov.my"
        )
        story.append(Paragraph(citation_text, styles["Normal"]))

        # Build PDF
        doc.build(story)

    # Additional export helpers
    @staticmethod
    def comments_to_excel(comments, path):
        """Export a list of comment dicts to an Excel file."""
        try:
            df = pd.DataFrame(comments)
            # If the expected columns exist, reorder to the final specification
            expected_cols = [
                "Thread ID", "Date", "Post Type", "Thread Title", "Thread URL",
                "Author", "Comment", "Upvotes"
            ]
            for col in expected_cols:
                if col not in df.columns:
                    raise KeyError(
                        f"Column '{col}' missing from exported data. Ensure comments dicts have all required keys."
                    )
            df = df[expected_cols]
            df.to_excel(path, index=False)
        except Exception as exc:
            raise RuntimeError(f"Failed to save comments to Excel: {exc}")

    @staticmethod
    def all_threads_to_excel(posts, path):
        """Export comments from all threads to an Excel file."""
        all_data = []
        # Assign a unique thread ID (T1, T2, ...) per thread
        for i, sub in enumerate(posts, start=1):
            thread_id = f"T{i}"
            # Determine post type according to Reddit metadata
            try:
                # Poll type
                if getattr(sub, "poll_data", None) is not None:
                    post_type = "Poll"
                # Text post
                elif getattr(sub, "is_self", False):
                    post_type = "Text"
                else:
                    hint = getattr(sub, "post_hint", None)
                    url = getattr(sub, "url", "").lower()
                    if hint == "image" or url.endswith((".jpg", ".png", ".gif")):
                        post_type = "Image"
                    elif hint in ("hosted:video", "rich:video"):
                        post_type = "Video"
                    elif hint == "link":
                        post_type = "Link"
                    else:
                        post_type = "Other"
            except Exception:
                post_type = "Other"
            # Replace more comments
            try:
                sub.comments.replace_more(limit=None)
            except Exception:
                pass
            for c in sub.comments.list():
                all_data.append({
                    "Thread ID": thread_id,
                    "Date": datetime.utcfromtimestamp(getattr(c, 'created_utc', time.time())).strftime('%Y-%m-%d %H:%M:%S'),
                    "Post Type": post_type,
                    "Thread Title": sub.title,
                    "Thread URL": getattr(sub, 'url', ''),
                    "Author": str(c.author),
                    "Comment": c.body if c.body else '',
                    "Upvotes": c.score
                })
        try:
            df = pd.DataFrame(all_data)
            # Order columns as specified
            cols = [
                "Thread ID", "Date", "Post Type", "Thread Title", "Thread URL", "Author", "Comment", "Upvotes"
            ]
            df = df[cols]
            df.to_excel(path, index=False)
        except Exception as exc:
            raise RuntimeError(f"Failed to save all threads' comments to Excel: {exc}")


# =====================================================
# GUI
# =====================================================

class GUI:
    """Tkinter GUI for RedScrap.  Allows input of scraping parameters and report generation."""

    def __init__(self, reddit):
        self.reddit = reddit
        self.posts = []
        self.root = tk.Tk()
        # Set a simplified window title
        self.root.title(f"RedScrap v{__version__}")
        self.root.geometry("800x600")

        # Input fields
        tk.Label(self.root, text="Subreddit:").pack(anchor='w')
        self.subreddit_entry = tk.Entry(self.root, width=50)
        self.subreddit_entry.insert(0, "malaysia")
        self.subreddit_entry.pack(fill='x', padx=5)
        tk.Label(self.root, text="Keywords (comma separated):").pack(anchor='w')
        self.keyword_entry = tk.Entry(self.root, width=50)
        self.keyword_entry.pack(fill='x', padx=5)
        tk.Label(self.root, text="Start Date (YYYY-MM-DD):").pack(anchor='w')
        self.start_entry = tk.Entry(self.root, width=20)
        self.start_entry.insert(0, "2015-01-01")
        self.start_entry.pack(padx=5)
        tk.Label(self.root, text="End Date (YYYY-MM-DD):").pack(anchor='w')
        self.end_entry = tk.Entry(self.root, width=20)
        self.end_entry.insert(0, "2024-12-31")
        self.end_entry.pack(padx=5)
        tk.Button(self.root, text="Search Threads", command=self.search_threads, bg="#2196F3", fg="white").pack(pady=10)

        # Listbox to display threads
        tk.Label(self.root, text="Matching Threads:").pack(anchor='w')
        frame = tk.Frame(self.root)
        frame.pack(fill='both', expand=True)
        scrollbar = Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox = Listbox(frame, width=90, yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar.config(command=self.listbox.yview)

        # Summary label (quick summary info)
        # Center the quick summary line across the window and keep it blue
        self.summary_label = tk.Label(
            self.root,
            text="",
            fg="blue",
            anchor='center',
            justify='center'
        )
        # Fill horizontally so the text can center properly
        self.summary_label.pack(fill='x', pady=5)

        # Buttons for scraping and reporting in a single horizontal frame
        # All long‑running operations are kicked off via start_* methods defined below
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)
        # Reorder buttons: Early Report, Scrape Selected Thread, Scrape All Threads
        # Assign colours: Early Report (yellow), Scrape Selected (yellow), Scrape All (green)
        self.report_btn = tk.Button(
            button_frame,
            text="Early Report",
            command=self.start_generate_report,
            bg="#FFD700",
            fg="black"
        )
        self.report_btn.pack(side=tk.LEFT, padx=5)
        self.scrape_selected_btn = tk.Button(
            button_frame,
            text="Scrape Selected Thread",
            command=self.start_scrape_selected,
            bg="#FFD700",
            fg="black"
        )
        self.scrape_selected_btn.pack(side=tk.LEFT, padx=5)
        self.scrape_all_btn = tk.Button(
            button_frame,
            text="Scrape All Threads",
            command=self.start_scrape_all,
            bg="#4CAF50",
            fg="white"
        )
        self.scrape_all_btn.pack(side=tk.LEFT, padx=5)

        # Remove the old citation footer.  The support email will be displayed below instead.

        # Progress bar and Cancel button
        progress_frame = tk.Frame(self.root)
        progress_frame.pack(fill='x', padx=5, pady=5)
        # Use ttk progress bar if available
        if HAS_TK and ttk is not None:
            self.progress = ttk.Progressbar(progress_frame, orient='horizontal', mode='indeterminate')
            self.progress.pack(side=tk.LEFT, fill='x', expand=True)
        else:
            self.progress = None
        self.cancel_button = tk.Button(progress_frame, text="Cancel", command=self.cancel_task)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        # Support email text in place of the old footer and log panel.
        # Centre the support email text horizontally with small grey font.
        self.support_label = tk.Label(
            self.root,
            text="Support email: saprimad@moh.gov.my",
            font=("Arial", 8),
            fg="gray",
            anchor='center',
            justify='center'
        )
        # Pack after the progress bar to appear at the bottom of the window
        self.support_label.pack(fill='x', padx=5, pady=5)



        # Internal state for cancellation
        self.cancel_requested = False

    def search_threads(self):
        """Fetch threads based on user input and populate the listbox."""
        sub = self.subreddit_entry.get().strip()
        kws = [k.strip() for k in self.keyword_entry.get().split(',') if k.strip()]
        start = self.start_entry.get().strip()
        end = self.end_entry.get().strip()
        if not sub:
            messagebox.showerror("Error", "Please enter a subreddit.")
            return
        # Validate keyword field (should not be empty)
        if not kws:
            messagebox.showerror("Error", "Please enter at least one keyword.")
            return
        # Validate date formats
        for date_str in [start, end]:
            if date_str:
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Error", f"Invalid date format: {date_str}. Use YYYY-MM-DD.")
                    return
        try:
            scraper = Scraper(self.reddit, sub, kws, start, end)
            self.posts = scraper.fetch_threads(limit=200)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while searching: {e}")
            return
        # Populate listbox
        self.listbox.delete(0, tk.END)
        for subm in self.posts:
            title = subm.title if len(subm.title) <= 80 else subm.title[:77] + '...'
            self.listbox.insert(tk.END, f"{title} ({subm.num_comments} comments)")

        # Update summary info
        self.update_summary()

    # ------------------------------------------------------------------
    # Long‑running tasks wrappers and implementations
    # These functions spawn separate threads to avoid freezing the GUI.
    # They also start/stop the progress bar, log status messages, and
    # respect the cancellation flag.
    # ------------------------------------------------------------------

    def start_scrape_selected(self):
        """Validate input and start scraping the selected thread in a thread."""
        # Ensure there are posts and a selection
        if not self.posts:
            messagebox.showerror("Error", "No threads available. Please search first.")
            return
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showerror("Error", "Please select a thread to scrape.")
            return
        # Ask for a save path before spawning the thread (must occur in the main thread)
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if not path:
            return
        # Start the scraping thread
        thread = threading.Thread(target=self.scrape_selected_task, args=(sel[0], path), daemon=True)
        thread.start()

    def scrape_selected_task(self, index: int, path: str):
        """Perform the scraping of a single thread and save to Excel."""
        # Reset cancellation flag
        self.cancel_requested = False
        # Start progress bar if available
        if self.progress is not None:
            try:
                self.progress.start()
            except Exception:
                pass
        # Log start
        self.log_message("Starting scrape of selected thread...")
        try:
            sub = self.posts[index]
            # Compute thread ID based on index (T1, T2, ...)
            thread_id = f"T{index + 1}"
            # Determine post type for this thread
            try:
                if getattr(sub, "poll_data", None) is not None:
                    post_type = "Poll"
                elif getattr(sub, "is_self", False):
                    post_type = "Text"
                else:
                    hint = getattr(sub, "post_hint", None)
                    url = getattr(sub, "url", "").lower()
                    if hint == "image" or url.endswith((".jpg", ".png", ".gif")):
                        post_type = "Image"
                    elif hint in ("hosted:video", "rich:video"):
                        post_type = "Video"
                    elif hint == "link":
                        post_type = "Link"
                    else:
                        post_type = "Other"
            except Exception:
                post_type = "Other"
            # Collect comments; check for cancellation periodically
            comments = []
            try:
                sub.comments.replace_more(limit=None)
            except Exception:
                pass
            for j, c in enumerate(sub.comments.list()):
                if self.cancel_requested:
                    self.log_message("Scrape cancelled by user.")
                    break
                comments.append({
                    "Thread ID": thread_id,
                    "Date": datetime.utcfromtimestamp(getattr(c, 'created_utc', time.time())).strftime('%Y-%m-%d %H:%M:%S'),
                    "Post Type": post_type,
                    "Thread Title": sub.title,
                    "Thread URL": getattr(sub, 'url', ''),
                    "Author": str(c.author),
                    "Comment": c.body if c.body else '',
                    "Upvotes": c.score
                })
                # Log every 100 comments to avoid flooding
                if (j + 1) % 100 == 0:
                    self.log_message(f"Fetched {j + 1} comments...")
            # If not cancelled, save to Excel
            if not self.cancel_requested:
                # Use Exporter helper to reorder and save
                Exporter.comments_to_excel(comments, path)
                # Use the GUI thread to show success message
                self.root.after(0, lambda: messagebox.showinfo("Success", f"Comments saved to {path}"))
                self.log_message("Selected thread scrape completed successfully.")
        except Exception as exc:
            # Show error message in the GUI thread
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to scrape selected thread: {exc}"))
            self.log_message(f"Error scraping selected thread: {exc}")
        finally:
            # Stop progress bar and clear cancellation flag
            if self.progress is not None:
                try:
                    self.progress.stop()
                except Exception:
                    pass
            self.cancel_requested = False

    def start_scrape_all(self):
        """Validate input and start scraping all threads in a thread."""
        if not self.posts:
            messagebox.showerror("Error", "No threads available. Please search first.")
            return
        # Ask for save path in main thread
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if not path:
            return
        # Start the scraping thread
        thread = threading.Thread(target=self.scrape_all_task, args=(path,), daemon=True)
        thread.start()

    def scrape_all_task(self, path: str):
        """Scrape comments from all threads and save to Excel."""
        self.cancel_requested = False
        if self.progress is not None:
            try:
                self.progress.start()
            except Exception:
                pass
        self.log_message("Starting scrape of all threads...")
        try:
            all_data = []
            for i, sub in enumerate(self.posts, start=1):
                if self.cancel_requested:
                    self.log_message("Scrape cancelled by user.")
                    break
                # Determine thread ID
                thread_id = f"T{i}"
                # Determine post type
                try:
                    if getattr(sub, "poll_data", None) is not None:
                        post_type = "Poll"
                    elif getattr(sub, "is_self", False):
                        post_type = "Text"
                    else:
                        hint = getattr(sub, "post_hint", None)
                        url = getattr(sub, "url", "").lower()
                        if hint == "image" or url.endswith((".jpg", ".png", ".gif")):
                            post_type = "Image"
                        elif hint in ("hosted:video", "rich:video"):
                            post_type = "Video"
                        elif hint == "link":
                            post_type = "Link"
                        else:
                            post_type = "Other"
                except Exception:
                    post_type = "Other"
                try:
                    sub.comments.replace_more(limit=None)
                except Exception:
                    pass
                for j, c in enumerate(sub.comments.list()):
                    if self.cancel_requested:
                        break
                    all_data.append({
                        "Thread ID": thread_id,
                        "Date": datetime.utcfromtimestamp(getattr(c, 'created_utc', time.time())).strftime('%Y-%m-%d %H:%M:%S'),
                        "Post Type": post_type,
                        "Thread Title": sub.title,
                        "Thread URL": getattr(sub, 'url', ''),
                        "Author": str(c.author),
                        "Comment": c.body if c.body else '',
                        "Upvotes": c.score
                    })
                    # Log progress every 500 comments
                    if (j + 1) % 500 == 0:
                        self.log_message(f"Scraped {j + 1} comments from thread {i}...")
            if not self.cancel_requested:
                df = pd.DataFrame(all_data)
                try:
                    cols = [
                        "Thread ID", "Date", "Post Type", "Thread Title", "Thread URL",
                        "Author", "Comment", "Upvotes"
                    ]
                    df = df[cols]
                    df.to_excel(path, index=False)
                    self.root.after(0, lambda: messagebox.showinfo("Success", f"All threads' comments saved to {path}"))
                    self.log_message("All threads scrape completed successfully.")
                except Exception as exc:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to save all threads' comments: {exc}"))
                    self.log_message(f"Error saving all threads' comments: {exc}")
        except Exception as exc:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to scrape all threads: {exc}"))
            self.log_message(f"Error scraping all threads: {exc}")
        finally:
            if self.progress is not None:
                try:
                    self.progress.stop()
                except Exception:
                    pass
            self.cancel_requested = False

    def start_generate_report(self):
        """Validate input and start report generation in a thread."""
        if not self.posts:
            messagebox.showerror("Error", "No threads to analyze. Please search first.")
            return
        # Ask for save path
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if not path:
            return
        # Start the thread to generate report
        thread = threading.Thread(target=self.generate_report_task, args=(path,), daemon=True)
        thread.start()

    def generate_report_task(self, path: str):
        """Generate the PDF report in a background thread."""
        self.cancel_requested = False
        if self.progress is not None:
            try:
                self.progress.start()
            except Exception:
                pass
        self.log_message("Starting report generation...")
        try:
            # Analyzer and meta should be prepared in the thread, but heavy computation may take time
            analyzer = Analyzer(self.posts)
            meta = {
                "subreddit": self.subreddit_entry.get().strip(),
                "keywords": [k.strip() for k in self.keyword_entry.get().split(',') if k.strip()],
                "start_date": self.start_entry.get().strip(),
                "end_date": self.end_entry.get().strip(),
            }
            if not self.cancel_requested:
                Exporter.generate_pdf_enhanced(self.posts, analyzer, path, meta)
                # success message
                self.root.after(0, lambda: messagebox.showinfo("Success", f"Early report saved to {path}"))
                self.log_message("Report generated successfully.")
        except Exception as exc:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to generate report: {exc}"))
            self.log_message(f"Error generating report: {exc}")
        finally:
            if self.progress is not None:
                try:
                    self.progress.stop()
                except Exception:
                    pass
            self.cancel_requested = False

    def generate_report(self):
        """Generate the enhanced report based on current posts."""
        if not self.posts:
            messagebox.showerror("Error", "No threads to analyze. Please search first.")
            return
        # Analyzer now automatically attempts sentiment analysis on initialization
        analyzer = Analyzer(self.posts) 
        # Collect metadata
        meta = {
            "subreddit": self.subreddit_entry.get().strip(),
            "keywords": [k.strip() for k in self.keyword_entry.get().split(',') if k.strip()],
            "start_date": self.start_entry.get().strip(),
            "end_date": self.end_entry.get().strip(),
        }
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if path:
            try:
                Exporter.generate_pdf_enhanced(self.posts, analyzer, path, meta)
                messagebox.showinfo("Success", f"Early report saved to {path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate report: {e}")
    
    # New helper to update the summary label
    def update_summary(self):
        total_threads = len(self.posts)
        total_comments = sum(getattr(sub, 'num_comments', 0) for sub in self.posts)
        total_upvotes = sum(getattr(sub, 'score', 0) for sub in self.posts)
        avg_comments = round(total_comments / total_threads, 2) if total_threads else 0
        summary = (f"Found {total_threads} threads | ~{total_comments} comments | ~{total_upvotes} upvotes\n"
                   f"Average comments/thread: {avg_comments}")
        self.summary_label.config(text=summary)

    # Helper to log messages with timestamp
    def log_message(self, message: str):
        """
        Log messages with timestamps.

        In the GUI version, we no longer display a log panel. Instead, we
        simply print messages to the console. This keeps the method
        functional for debugging without altering the user interface.
        """
        timestamp = datetime.now().strftime("%H:%M")
        print(f"[{timestamp}] {message}")

    # Cancel current task
    def cancel_task(self):
        self.cancel_requested = True
        self.log_message("Cancellation requested...")
        if self.progress is not None:
            try:
                self.progress.stop()
            except Exception:
                pass

    def scrape_selected(self):
        """Export comments from the selected thread to an Excel file."""
        # Validate there is a search result and a selection
        if not self.posts:
            messagebox.showerror("Error", "No threads available. Please search first.")
            return
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showerror("Error", "Please select a thread to scrape.")
            return
        sub = self.posts[sel[0]]
        # Determine thread ID based on selection (1-indexed)
        thread_id = f"T{sel[0] + 1}"
        # Determine post type according to Reddit metadata
        try:
            if getattr(sub, "poll_data", None) is not None:
                post_type = "Poll"
            elif getattr(sub, "is_self", False):
                post_type = "Text"
            else:
                hint = getattr(sub, "post_hint", None)
                url = getattr(sub, "url", "").lower()
                if hint == "image" or url.endswith((".jpg", ".png", ".gif")):
                    post_type = "Image"
                elif hint in ("hosted:video", "rich:video"):
                    post_type = "Video"
                elif hint == "link":
                    post_type = "Link"
                else:
                    post_type = "Other"
        except Exception:
            post_type = "Other"
        # Collect comments for selected thread with new columns
        comments = []
        try:
            sub.comments.replace_more(limit=None)
        except Exception:
            pass
        for c in sub.comments.list():
            comments.append({
                "Thread ID": thread_id,
                "Date": datetime.utcfromtimestamp(getattr(c, 'created_utc', time.time())).strftime('%Y-%m-%d %H:%M:%S'),
                "Post Type": post_type,
                "Thread Title": sub.title,
                "Thread URL": getattr(sub, 'url', ''),
                "Author": str(c.author),
                "Comment": c.body if c.body else '',
                "Upvotes": c.score
            })
        # Choose a save location
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if path:
            try:
                Exporter.comments_to_excel(comments, path)
                messagebox.showinfo("Success", f"Comments saved to {path}")
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

    def scrape_all(self):
        """Export comments from all threads to an Excel file."""
        if not self.posts:
            messagebox.showerror("Error", "No threads available. Please search first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if path:
            try:
                Exporter.all_threads_to_excel(self.posts, path)
                messagebox.showinfo("Success", f"All threads' comments saved to {path}")
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

    def run(self):
        self.root.mainloop()


# =====================================================
# Main entry point
# =====================================================

if __name__ == "__main__":
    reddit = get_reddit()
    # Only launch the GUI if tkinter is available. Otherwise, inform the user.
    if HAS_TK and tk is not None:
        gui = GUI(reddit)
        gui.run()
    else:
        print(
            "tkinter is not available. The GUI cannot be launched. You can still use the"
            " scraping and analysis classes programmatically in a Python environment, or "
            "install the Tk libraries (e.g. python3-tk) to enable the GUI."
        )
