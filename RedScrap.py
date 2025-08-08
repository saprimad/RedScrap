import praw
import tkinter as tk
from tkinter import messagebox, filedialog, Listbox, Scrollbar, Label
import pandas as pd
from datetime import datetime
import time
from collections import Counter, defaultdict

# Reddit API config
reddit = praw.Reddit(
    client_id='HhDiAAe64t2GPbIaMcOmUA',
    client_secret='7FpHy9omPWGiJIickcDpU1p0-Xc9nA',
    user_agent='reddit_scraper_public',
    check_for_async=False,
    config_interpolation="basic"
)

def search_threads():
    kws = keyword_entry.get().strip()
    subreddit_name = subreddit_entry.get().strip()
    start_date_str = start_entry.get().strip()
    end_date_str   = end_entry.get().strip()

    # parse up to 3 keywords
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
    global posts
    posts = []

    try:
        total_comments    = 0
        total_upvotes     = 0
        year_thread_counts  = Counter()
        year_comment_counts = defaultdict(int)

        for submission in reddit.subreddit(subreddit_name).search(query, sort="new", limit=200):
            created = int(submission.created_utc)
            if start_ts <= created <= end_ts:
                y = datetime.utcfromtimestamp(created).year
                posts.append(submission)
                total_comments    += submission.num_comments
                total_upvotes     += submission.score
                year_thread_counts[y]  += 1
                year_comment_counts[y] += submission.num_comments
                listbox.insert(tk.END, f"{submission.title} ({datetime.utcfromtimestamp(created).date()})")

        if not posts:
            messagebox.showinfo("No results", "No matching threads.")
            count_label.config(text="")
        else:
            avg_comments = round(total_comments / len(posts), 1)
            parts = [f"{y}: {year_thread_counts[y]} threads, {year_comment_counts[y]} comments"
                     for y in sorted(year_thread_counts)]
            year_display = "; ".join(parts)
            count_label.config(text=
                f"Found {len(posts)} threads | ~{total_comments} comments | ~{total_upvotes} upvotes\n"
                f"Average comments/thread: {avg_comments}\n"
                f"Threads by year: {year_display}"
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

# —— GUI Setup ——
root = tk.Tk()
root.title("Reddit Scraper – Multi-Keyword")
root.geometry("720x700")

tk.Label(root, text="Subreddit (e.g. malaysia):").pack(pady=(10,0))
subreddit_entry = tk.Entry(root, width=50); subreddit_entry.insert(0,"malaysia"); subreddit_entry.pack()

tk.Label(root, text="Keywords (comma-separated, up to 3):").pack(pady=(10,0))
keyword_entry = tk.Entry(root, width=50); keyword_entry.pack()

tk.Label(root, text="Start Date (YYYY-MM-DD):").pack(pady=(10,0))
start_entry = tk.Entry(root, width=20); start_entry.insert(0,"2015-01-01"); start_entry.pack()

tk.Label(root, text="End Date (YYYY-MM-DD):").pack(pady=(10,0))
end_entry   = tk.Entry(root, width=20); end_entry.insert(0,"2024-12-31");   end_entry.pack()

tk.Button(root, text="Search Threads", command=search_threads).pack(pady=10)

tk.Label(root, text="Matching Threads:").pack()
frame = tk.Frame(root); frame.pack()
sb = Scrollbar(frame); sb.pack(side=tk.RIGHT,fill=tk.Y)
listbox = Listbox(frame, width=90, height=15, yscrollcommand=sb.set)
listbox.pack(side=tk.LEFT,fill=tk.BOTH); sb.config(command=listbox.yview)

count_label = Label(root, text="", fg="blue", justify="left", wraplength=700)
count_label.pack(pady=5)

tk.Button(root, text="Scrape Selected Thread & Save", command=scrape_selected_thread).pack(pady=10)

# citation
tk.Label(root,
    text=("📌 Cite this tool:\n"
          "Tumiran, M. S., Abd Wahab, M. S., Jamal, J. A., & Othman, N. (2025). "
          "RedScrap: Python Tool for Netnographic Data Collection (v1.0.0). "
          "Zenodo. https://doi.org/10.5281/zenodo.16756945"),
    fg="gray", font=("Arial",9), justify="center", wraplength=700
).pack(pady=10)

root.mainloop()
