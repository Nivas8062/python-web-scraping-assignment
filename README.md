Python Web Scraping Interview Assignment
Overview
This project implements a reusable Python pipeline that scrapes the two public practice websites required by the assignment:
Books to Scrape: https://books.toscrape.com/
Quotes to Scrape: https://quotes.toscrape.com/
The pipeline follows scrape → clean → validate → deduplicate → consolidate → output.
Python version
Python 3.10+ recommended.
Setup
```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
```
Run
```bash
python main.py
```
Optional request delay:
```bash
python main.py --delay 0.5
```
The run creates:
`output/final_dataset.csv`
`output/summary_report.json`
`logs/scraper.log`
Scraping design
Books
`books_scraper.py` discovers pages through the site's `Next` link rather than hard-coding page numbers. Each listing card provides the title, price, availability, rating and product URL. The product page is then used to enrich the category and description.
Quotes
`quotes_scraper.py` follows the `Next` link until pagination ends. It extracts quote text, author, tags and the author URL. The author page is used to enrich the author description when available.
Standardized data model
Field	Purpose
source	Original source name
source_url	Original record URL
name_or_title	Book title or quote text
category	Book category; null for quotes
price	Numeric book price; null for quotes
rating	Integer 1–5 for books; null for quotes
author	Quote author; null for books
tags	Comma-separated normalized tags
description	Book description or author description
availability	Book availability; null for quotes
scraped_at	UTC timestamp for the run
Missing fields remain null. No data is invented.
Cleaning
Cleaning is separated from scraping. It removes extra whitespace, converts prices to numeric values, converts word ratings (`One`–`Five`) to integers, normalizes tags, and validates HTTP/HTTPS URLs.
Validation
Records are rejected when they have an unknown source, missing/invalid source URL, missing title/text, non-numeric price, or rating outside 1–5.
Deduplication
Duplicate keys are built from:
normalized source
normalized name/title
normalized author
Normalization uses Unicode normalization, case folding, whitespace normalization and trimming. Source is included so an identical string from different sources is not incorrectly removed.
Error handling and reliability
Request timeout handling
HTTP error handling
Retry strategy for connection/read errors and common 5xx/429 responses
Per-record parsing exception handling
Per-source exception isolation so one source failure does not automatically stop the other source
File and console logging
Configurable request delay to avoid unnecessarily aggressive traffic
Testing
Run:
```bash
pytest -q
```
The tests cover cleaning, validation and duplicate detection without making network requests.
Assumptions
The two sites retain the public HTML structures used by the scraper.
A record's source URL is the product URL for books and the author URL for quotes when available.
Quote `description` represents the author biography; this is source-specific enrichment.
The assignment's common schema permits null values for fields that do not apply to a source.
Known limitations
The scraper depends on the public HTML structure of the practice sites; selector changes would require updates.
Enriching every book and quote author requires additional requests, so the configured delay affects total runtime.
This is an interview assignment, not a distributed production crawler.
AI usage
See `AI_USAGE.md` for the required disclosure.
