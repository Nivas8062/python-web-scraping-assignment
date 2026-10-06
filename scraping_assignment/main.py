from __future__ import annotations
import argparse
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from scrapers.books_scraper import scrape_books, enrich_book
from scrapers.quotes_scraper import scrape_quotes, enrich_quote
from processing.cleaning import clean_record
from processing.validation import validate_record
from processing.deduplication import deduplicate

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"
LOG_DIR = ROOT / "logs"

SCHEMA = [
    "source", "source_url", "name_or_title", "category", "price", "rating",
    "author", "tags", "description", "availability", "scraped_at"
]


def configure_logging() -> logging.Logger:
    LOG_DIR.mkdir(exist_ok=True)
    logger = logging.getLogger("scraper")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    fh = logging.FileHandler(LOG_DIR / "scraper.log", encoding="utf-8")
    sh = logging.StreamHandler()
    fh.setFormatter(fmt); sh.setFormatter(fmt)
    logger.addHandler(fh); logger.addHandler(sh)
    return logger


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "PythonScrapingInterviewAssignment/1.0 (educational use)"
    })
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetcher_factory(delay: float):
    last_request = [0.0]

    def fetch(session, url, logger) -> Optional[BeautifulSoup]:
        elapsed = time.monotonic() - last_request[0]
        if elapsed < delay:
            time.sleep(delay - elapsed)
        try:
            response = session.get(url, timeout=(10, 30))
            last_request[0] = time.monotonic()
            response.raise_for_status()
            return BeautifulSoup(response.content, "html.parser")
        except requests.RequestException as exc:
            last_request[0] = time.monotonic()
            logger.error("Request failed: %s | %s", url, exc)
            return None
        except Exception as exc:
            last_request[0] = time.monotonic()
            logger.exception("Unexpected fetch failure: %s | %s", url, exc)
            return None
    return fetch


def process_source(raw_records, source_name, session, fetcher, logger, scraped_at):
    cleaned = []
    rejected = []
    for raw in raw_records:
        try:
            if source_name == "Books to Scrape":
                raw = enrich_book(session, fetcher, logger, raw)
            else:
                raw = enrich_quote(session, fetcher, logger, raw)
            record = clean_record(raw, scraped_at)
            valid, errors = validate_record(record)
            if valid:
                cleaned.append(record)
            else:
                rejected.append({"record": record, "errors": errors})
        except Exception as exc:
            logger.exception("Record processing failure from %s: %s", source_name, exc)
            rejected.append({"record": raw, "errors": ["processing_exception"]})
    return cleaned, rejected


def run(delay: float = 0.25):
    logger = configure_logging()
    OUTPUT_DIR.mkdir(exist_ok=True)
    started = time.perf_counter()
    scraped_at = datetime.now(timezone.utc).isoformat()
    session = build_session()
    fetcher = fetcher_factory(delay)

    raw_counts = {"Books to Scrape": 0, "Quotes to Scrape": 0}
    cleaned_counts = {"Books to Scrape": 0, "Quotes to Scrape": 0}
    rejected = []
    all_cleaned = []

    for source_name, scraper in [
        ("Books to Scrape", scrape_books),
        ("Quotes to Scrape", scrape_quotes),
    ]:
        logger.info("Starting source: %s", source_name)
        try:
            raw = list(scraper(session, fetcher, logger))
            raw_counts[source_name] = len(raw)
            logger.info("Collected %d raw records from %s", len(raw), source_name)
            cleaned, source_rejected = process_source(raw, source_name, session, fetcher, logger, scraped_at)
            cleaned_counts[source_name] = len(cleaned)
            rejected.extend(source_rejected)
            all_cleaned.extend(cleaned)
        except Exception:
            logger.exception("Source failed but pipeline will continue: %s", source_name)

    unique, duplicates = deduplicate(all_cleaned)
    df = pd.DataFrame(unique)
    for col in SCHEMA:
        if col not in df.columns:
            df[col] = None
    df = df[SCHEMA]
    csv_path = OUTPUT_DIR / "final_dataset.csv"
    df.to_csv(csv_path, index=False)

    duration = round(time.perf_counter() - started, 3)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "execution_time_seconds": duration,
        "sources": raw_counts,
        "records_collected_total": sum(raw_counts.values()),
        "records_after_cleaning": sum(cleaned_counts.values()),
        "records_rejected_validation_or_processing": len(rejected),
        "duplicates_detected_removed": len(duplicates),
        "final_record_count": len(unique),
        "output_file": str(csv_path.relative_to(ROOT)),
        "validation_rejections": rejected[:100],
        "duplicate_examples": duplicates[:20],
    }
    with (OUTPUT_DIR / "summary_report.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logger.info("Pipeline complete. Final records: %d", len(unique))
    logger.info("Summary: %s", OUTPUT_DIR / "summary_report.json")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-source scraping assignment pipeline")
    parser.add_argument("--delay", type=float, default=0.25, help="Seconds between requests")
    args = parser.parse_args()
    run(delay=max(0.0, args.delay))
