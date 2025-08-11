
import praw
import tkinter as tk
from tkinter import messagebox, filedialog, Listbox, Scrollbar, Label
import pandas as pd
from datetime import datetime
import time
from collections import Counter, defaultdict
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.barcharts import VerticalBarChart

# Reddit API config
reddit = praw.Reddit(
    client_id='HhDiAAe64t2GPbIaMcOmUA',
    client_secret='7FpHy9omPWGiJIickcDpU1p0-Xc9nA',
    user_agent='reddit_scraper_public',
    check_for_async=False,
    config_interpolation="basic"
)

posts = []
year_thread_counts = Counter()
year_comment_counts = defaultdict(int)

def search_threads():
    global posts, year_thread_counts, year_comment_counts
    kws = keyword_entry.get().strip()
    subreddit_name = subreddit_entry.get().strip()
    start_date_str = start_entry.get().strip()
    end_date_str   = end_entry.get().strip()

    keywords = [k.strip() for k in kws.split(',') if k.strip()][:3]
    if not keywords or not subreddit_name or not start_date_str or not end_date_str:
        messagebox.showwarning("Missing Input", "Enter up to 3 keywords, subreddit, and both dates.")
        return

    query = " OR ".join(keywords)
    try:
        start_ts = int(time.mktime(datetime.strptime(start_date_str, '%Y-%m-%d').timetuple()))
        end_ts   = int(time.mktime(datetime.strptime(end_date_str,   '%Y-%m-%d').timetuple()))
    except:
        messagebox.showerror("Date Error", "Use format YYYY-MM-DD")
        return

    listbox.delete(0, tk.END)
    posts = []
    year_thread_counts = Counter()
    year_comment_counts = defaultdict(int)

    try:
        total_comments = 0
        total_upvotes = 0

        for submission in reddit.subreddit(subreddit_name).search(query, sort="new", limit=200):
            created = int(submission.created_utc)
            if start_ts <= created <= end_ts:
                y = datetime.utcfromtimestamp(created).year
                posts.append(submission)
                total_comments += submission.num_comments
                total_upvotes += submission.score
                year_thread_counts[y] += 1
                year_comment_counts[y] += submission.num_comments
                listbox.insert(tk.END, f"{submission.title} ({datetime.utcfromtimestamp(created).date()}) - 💬 {submission.num_comments} comments")

        if not posts:
            messagebox.showinfo("No results", "No matching threads.")
            count_label.config(text="")
        else:
            avg_comments = round(total_comments / len(posts), 1)
            count_label.config(text=
                f"Found {len(posts)} threads | ~{total_comments} comments | ~{total_upvotes} upvotes\n"
                f"Average comments/thread: {avg_comments}"
            )
    except Exception as e:
        messagebox.showerror("Error", f"Search failed:\n{e}")

def scrape_selected_thread():
    try:
        sel = listbox.curselection()
        if not sel:
            messagebox.showwarning("No selection", "Select a thread.")
            return
        sub = posts[sel[0]]
        sub.comments.replace_more(limit=None)

        data = []
        for c in sub.comments.list():
            data.append({
                "Author": str(c.author),
                "Comment": c.body,
                "Upvotes": c.score,
                "Date": datetime.utcfromtimestamp(c.created_utc).strftime('%Y-%m-%d %H:%M:%S')
            })
        df = pd.DataFrame(data)
        path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                            filetypes=[("Excel files","*.xlsx")])
        if path:
            df.to_excel(path, index=False)
            messagebox.showinfo("Saved", f"File saved to:\n{path}\nExported {len(df)} comments.")
    except Exception as e:
        messagebox.showerror("Error", f"Scraping failed:\n{e}")

def scrape_all_threads():
    if not posts:
        messagebox.showwarning("No threads", "Please run a search first.")
        return

    all_data = []
    try:
        countdown_label.config(text=f"Starting to scrape {len(posts)} threads...")
        root.update()
        for i, sub in enumerate(posts):
            countdown_label.config(text=f"Scraping thread {i+1} of {len(posts)}: {sub.title[:50]}...")
            root.update()
            sub.comments.replace_more(limit=None)
            for c in sub.comments.list():
                all_data.append({
                    "Thread Title": sub.title,
                    "Thread URL": sub.url,
                    "Author": str(c.author),
                    "Comment": c.body,
                    "Upvotes": c.score,
                    "Date": datetime.utcfromtimestamp(c.created_utc).strftime('%Y-%m-%d %H:%M:%S')
                })

        if not all_data:
            messagebox.showinfo("No comments", "No comments found in the threads.")
            return

        df = pd.DataFrame(all_data)
        path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                            filetypes=[("Excel files", "*.xlsx")])
        if path:
            df.to_excel(path, index=False)
            messagebox.showinfo("Saved", f"All threads saved to:\n{path}\nTotal comments: {len(df)}")
    except Exception as e:
        messagebox.showerror("Error", f"Scraping all threads failed:\n{e}")

def generate_early_report():
    try:
        if not posts:
            messagebox.showwarning("No data", "Please search for threads first.")
            return

        subreddit = subreddit_entry.get().strip()
        keywords = keyword_entry.get().strip()
        start_date = start_entry.get().strip()
        end_date = end_entry.get().strip()
        summary_text = count_label.cget("text")
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not file_path:
            return

        doc = SimpleDocTemplate(file_path, pagesize=landscape(letter))
        styles = getSampleStyleSheet()
        wrapped_style = ParagraphStyle('wrapped', parent=styles['Normal'], alignment=TA_LEFT, wordWrap='CJK', fontSize=10)
        story = []

        story.append(Paragraph("📄 RedScrap Early Report", styles["Title"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Subreddit:</b> {subreddit}", styles["Normal"]))
        story.append(Paragraph(f"<b>Keywords:</b> {keywords}", styles["Normal"]))
        story.append(Paragraph(f"<b>Date Range:</b> {start_date} to {end_date}", styles["Normal"]))
        story.append(Paragraph(f"<b>Generated on:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
        story.append(Spacer(1, 12))

        # Summary table
        story.append(Paragraph("<b>📊 Thread & Comment Summary by Year</b>", styles["Heading3"]))
        summary_table = [["Year", "Threads", "Comments"]]
        for y in sorted(set(year_thread_counts) | set(year_comment_counts)):
            summary_table.append([str(y), str(year_thread_counts[y]), str(year_comment_counts[y])])
        table = Table(summary_table, colWidths=[80, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

        # Bar chart
        story.append(Paragraph("📉 Visual Summary (Threads = Blue, Comments = Red)", styles["Heading3"]))
        drawing = Drawing(500, 280)
        chart = VerticalBarChart()
        chart.x = 50
        chart.y = 50
        chart.height = 180
        chart.width = 400
        years = sorted(set(year_thread_counts.keys()) | set(year_comment_counts.keys()))
        thread_vals = [year_thread_counts.get(y, 0) for y in years]
        comment_vals = [year_comment_counts.get(y, 0) for y in years]
        chart.data = [thread_vals, comment_vals]
        chart.categoryAxis.categoryNames = [str(y) for y in years]
        chart.bars[0].fillColor = colors.blue
        chart.bars[1].fillColor = colors.red
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueStep = 50
        chart.valueAxis.valueMax = max(max(thread_vals), max(comment_vals)) + 50
        chart.categoryAxis.labels.angle = 45
        chart.categoryAxis.labels.dy = -15
        drawing.add(chart)
        story.append(drawing)
        story.append(PageBreak())

        story.append(Paragraph("<b>Thread Titles</b>", styles["Heading3"]))
        thread_data = [["No", "Thread Title + [Comments]", "Date"]]
        for i, sub in enumerate(posts):
            title = f"{sub.title}  [{sub.num_comments} comments]"
            thread_data.append([str(i+1), Paragraph(title, wrapped_style), datetime.utcfromtimestamp(sub.created_utc).strftime('%Y-%m-%d')])
        table = Table(thread_data, colWidths=[30, 440, 90])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('VALIGN', (0,0), (-1,-1), 'TOP')
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

        # Citation
        story.append(Paragraph("📌 Cite this tool:<br/>Tumiran, M. S., Abd Wahab, M. S., Jamal, J. A., & Othman, N. (2025). "
                               "RedScrap: Python Tool for Netnographic Data Collection (v1.1.4). "
                               "Zenodo. https://doi.org/10.5281/zenodo.16756945", styles["Italic"]))

        doc.build(story)
        messagebox.showinfo("Report Saved", f"Report saved to:\n{file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to generate report:\n{e}")

# GUI
root = tk.Tk()
root.title("RedScrap: Python Tool for Netnographic Data Collection Version 1.1.4")
root.geometry("740x740")

tk.Label(root, text="Subreddit (e.g. malaysia):").pack(pady=(10,0))
subreddit_entry = tk.Entry(root, width=50); subreddit_entry.insert(0,"malaysia"); subreddit_entry.pack()

tk.Label(root, text="Keywords (comma-separated, up to 3):").pack(pady=(10,0))
keyword_entry = tk.Entry(root, width=50); keyword_entry.pack()

tk.Label(root, text="Start Date (YYYY-MM-DD):").pack(pady=(10,0))
start_entry = tk.Entry(root, width=20); start_entry.insert(0,"2015-01-01"); start_entry.pack()

tk.Label(root, text="End Date (YYYY-MM-DD):").pack(pady=(10,0))
end_entry = tk.Entry(root, width=20); end_entry.insert(0,"2024-12-31"); end_entry.pack()

tk.Button(root, text="Search Threads", command=search_threads).pack(pady=10)

tk.Label(root, text="Matching Threads:").pack()
frame = tk.Frame(root); frame.pack()
sb = Scrollbar(frame); sb.pack(side=tk.RIGHT,fill=tk.Y)
listbox = Listbox(frame, width=90, height=15, yscrollcommand=sb.set)
listbox.pack(side=tk.LEFT,fill=tk.BOTH); sb.config(command=listbox.yview)

count_label = Label(root, text="", fg="blue", justify="left", wraplength=700)
count_label.pack(pady=5)

btn_frame = tk.Frame(root); btn_frame.pack(pady=10)
tk.Button(btn_frame, text="📄 Early Report", command=generate_early_report, bg="#d4af37", fg="black").pack(side=tk.LEFT, padx=10)
tk.Button(btn_frame, text="Scrape Selected Thread & Save", command=scrape_selected_thread).pack(side=tk.LEFT, padx=10)
tk.Button(btn_frame, text="Scrape All Threads & Save", command=scrape_all_threads, bg="#0078D4", fg="white").pack(side=tk.LEFT, padx=10)

countdown_label = Label(root, text="", fg="darkgreen", font=("Arial", 10))
countdown_label.pack()

tk.Label(root,
    text=("📌 Cite this tool:\n"
          "Tumiran, M. S., Abd Wahab, M. S., Jamal, J. A., & Othman, N. (2025). "
          "RedScrap: Python Tool for Netnographic Data Collection (v1.1.4). "
          "Zenodo. https://doi.org/10.5281/zenodo.16756945"),
    fg="gray", font=("Arial",9), justify="center", wraplength=700
).pack(pady=10)

root.mainloop()
