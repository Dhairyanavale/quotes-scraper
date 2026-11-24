# Quotes Web Scraper (`QuoteScraper`)

A polite, object-oriented Python web scraper built with `requests` and `beautifulsoup4` that crawls all pages of `quotes.toscrape.com`, extracts quotes, authors, and tags, exports the results to `quotes.json` and `quotes.txt`, and prints summary statistics.

## Project Files

- `scraper.py` — Implements the `QuoteScraper` class, `export_results()`, and `display_metrics()`.
- `quotes.json` — Formatted UTF-8 JSON dataset containing all 100 extracted quotes (`quote`, `author`, `tags`).
- `quotes.txt` — Human-readable numbered text file with each quote, author, and tag list.
- `README.md` — Setup instructions, source justification, and scraping rules.

## Setup & Execution

1. Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1