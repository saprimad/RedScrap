# RedScrap  
*A Python Tool for Netnographic Data Collection from Reddit*  

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)  
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16756945.svg)](https://doi.org/10.5281/zenodo.16756945)  

---

## Overview  
RedScrap is an open-source Python tool designed to support **netnographic and qualitative research** by enabling efficient Reddit data collection. It combines both **GUI and CLI interfaces**, making it accessible to researchers with varying levels of technical expertise.  

Originally developed as part of doctoral research in Pharmacy Practice at Universiti Teknologi MARA, RedScrap follows ethical practices aligned with Reddit’s developer policies. It is published under version **v1.0.0** via Zenodo.  

Zenodo Record: [https://zenodo.org/records/16756945](https://zenodo.org/records/16756945)  

---

## Key Features  
- **Flexible Data Collection**: Scrape individual threads, subreddit-wide searches, or bulk operations.  
- **Advanced Filtering**: Search by keywords, date ranges, and subreddit targeting.  
- **Dual Interfaces**:  
  - GUI (embedded within `RedScrap.py`) for non-technical users  
  - CLI for advanced users  
- **Data Export**: Save results to CSV, Excel, or JSON formats for integration with qualitative analysis software.  
- **Early Reporting**: Generate quick summaries before full data extraction.  
- **Rate Limiting**: Internal limiter of **200 threads per minute**, tested under stress conditions to ensure compliance with Reddit’s rules and prevent bot detection.  
- **Reproducibility**: Timestamped outputs and built-in citation footer.  

---

## Installation  

### Requirements  
- Python 3.9+  
- Dependencies (listed in `requirements.txt`):  
  - `praw`  
  - `python-dotenv`  
  - `pandas`  
  - `reportlab`  
  - `tkinter` (usually bundled with Python)  

### Setup  
1. Clone this repository:  
   ```bash
   git clone https://github.com/saprimad/RedScrap.git
   cd RedScrap
   ```  

2. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```  

3. (For public release) Create a `.env` file for Reddit API credentials:  
   ```ini
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_client_secret
   REDDIT_USER_AGENT=RedScrap/1.0.0 by Tumiran, M. S.
   ```  

   *(In the review/demo version, API keys may be preloaded for ease of testing.)*  

---

## Usage  

### GUI Mode  
Run:  
```bash
python RedScrap.py
```  
This opens the graphical interface with input fields for subreddit, keywords, and date range.  

### CLI Mode  
Example:  
```bash
python RedScrap.py --subreddit malaysia --keyword cannabis --start 2024-01-01 --end 2024-12-31 --output results.json
```  

---

## Documentation  
- **README Updated**: Includes latest installation instructions, configuration, and usage steps.  
- **Tutorial**: Step-by-step user guide forthcoming during the implementation stage for end users.  
- **Academic Publication**: Published version v1.0.0 on Zenodo. Proper citation information included.  

---

## Citation  
If you use RedScrap in academic work, please cite:  

Tumiran, M. S., Abd Wahab, M. S., Jamal, J. A., & Othman, N. (2025). *RedScrap: Python Tool for Netnographic Data Collection (v1.0.0)*. Zenodo. https://doi.org/10.5281/zenodo.16756945  

---

## License  
This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.  
