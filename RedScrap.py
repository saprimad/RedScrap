import praw
import tkinter as tk
from tkinter import messagebox, filedialog, Listbox, Scrollbar
import pandas as pd
from datetime import datetime
import time

# Safe Reddit API config
reddit = praw.Reddit(
    client_id='HhDiAAe64t2GPbIaMcOmUA',
    client_secret='7FpHy9omPWGiJIickcDpU1p0-Xc9nA',
    user_agent='reddit_scraper_public',
    check_for_async=False,
    config_interpolation="basic"
)

def search_threads():
    keyword = keyword_entry.get().strip()
    subreddit_name = subreddit_entry.get().strip()
    start_date_str = start_entry.get().strip()
    end_date_str = end_entry.get().strip()

    if not keyword or not subreddit_name or not start_date_str or not end_date_str:
        messagebox.showwarning("Missing Input", "Please fill in all fields.")
        return

    try:
        start_timestamp = int(time.mktime(datetime.strptime(start_date_str, '%Y-%m-%d').timetuple()))
        end_timestamp = int(time.mktime(datetime.strptime(end_date_str, '%Y-%m-%d').timetuple()))
    except:
        messagebox.showerror("Date Error", "Use format: YYYY-MM-DD")
        return

    listbox.delete(0, tk.END)
    global posts
    posts = []

    try:
        for submission in reddit.subreddit(subreddit_name).search(keyword, sort="new", limit=100):
            created = int(submission.created_utc)
            if start_timestamp <= created <= end_timestamp:
                posts.append(submission)
                listbox.insert(tk.END, f"{submission.title} ({datetime.utcfromtimestamp(created).date()})")

        if not posts:
            messagebox.showinfo("No results", "No matching threads in that date range.")
    except Exception as e:
        messagebox.showerror("Error", f"Search failed:\n{str(e)}")

def scrape_selected_thread():
    try:
        selected_index = listbox.curselection()
        if not selected_index:
            messagebox.showwarning("No selection", "Select a thread first.")
            return

        submission = posts[selected_index[0]]
        submission.comments.replace_more(limit=None)

        comments_data = []
        for comment in submission.comments.list():
            comments_data.append({
                "Author": str(comment.author),
                "Comment": comment.body,
                "Upvotes": comment.score,
                "Date": datetime.utcfromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S')
            })

        df = pd.DataFrame(comments_data)

        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                 filetypes=[("Excel files", "*.xlsx")],
                                                 title="Save as")
        if file_path:
            df.to_excel(file_path, index=False)
            messagebox.showinfo("Saved", f"File saved to:\n{file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Scraping failed:\n{str(e)}")

# GUI
root = tk.Tk()
root.title("Reddit Comment Scraper (Public)")
root.geometry("680x580")

tk.Label(root, text="Subreddit (e.g. malaysia):").pack(pady=(10, 0))
subreddit_entry = tk.Entry(root, width=50)
subreddit_entry.insert(0, "malaysia")
subreddit_entry.pack()

tk.Label(root, text="Keyword to search:").pack(pady=(10, 0))
keyword_entry = tk.Entry(root, width=50)
keyword_entry.pack()

tk.Label(root, text="Start Date (YYYY-MM-DD):").pack(pady=(10, 0))
start_entry = tk.Entry(root, width=20)
start_entry.insert(0, "2023-01-01")
start_entry.pack()

tk.Label(root, text="End Date (YYYY-MM-DD):").pack(pady=(10, 0))
end_entry = tk.Entry(root, width=20)
end_entry.insert(0, "2023-12-31")
end_entry.pack()

tk.Button(root, text="Search Threads", command=search_threads).pack(pady=10)

tk.Label(root, text="Matching Threads:").pack()
frame = tk.Frame(root)
frame.pack()

scrollbar = Scrollbar(frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

listbox = Listbox(frame, width=90, height=15, yscrollcommand=scrollbar.set)
listbox.pack(side=tk.LEFT, fill=tk.BOTH)
scrollbar.config(command=listbox.yview)

tk.Button(root, text="Scrape Selected Thread & Save", command=scrape_selected_thread).pack(pady=20)

root.mainloop()
