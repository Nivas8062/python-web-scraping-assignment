from __future__ import annotations
from typing import Iterator
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
START_URL = urljoin(BASE_URL, "catalogue/page-1.html")


def _text(node) -> str:
    if not node:
        return ""

    text = " ".join(node.stripped_strings)

    # Books to Scrape includes this marker at the end
    # of some long descriptions.
    text = text.replace("...more", "").strip()

    return text


def _rating(node) -> str | None:
    if not node:
        return None
    classes = node.get("class", [])
    for value in ("One", "Two", "Three", "Four", "Five"):
        if value in classes:
            return value
    return None


def scrape_books(session: requests.Session, fetcher, logger) -> Iterator[dict]:
    """Yield one standardized-ish raw record per book. Pagination is discovered from Next links."""
    next_url = START_URL
    seen_pages = set()

    while next_url and next_url not in seen_pages:
        seen_pages.add(next_url)
        soup = fetcher(session, next_url, logger)
        if soup is None:
            logger.error("Skipping failed books page: %s", next_url)
            next_url = None if len(seen_pages) == 1 else None
            continue

        for card in soup.select("article.product_pod"):
            try:
                link = card.select_one("h3 a")
                if not link:
                    logger.warning("Book card missing title/link on %s", next_url)
                    continue
                product_url = urljoin(next_url, link.get("href", ""))
                availability = _text(card.select_one(".availability")) or None
                price_text = _text(card.select_one(".price_color")) or None
                rating = _rating(card.select_one(".star-rating"))
                yield {
                    "source": "Books to Scrape",
                    "source_url": product_url,
                    "name_or_title": _text(link),
                    "category": None,
                    "price": price_text,
                    "rating": rating,
                    "author": None,
                    "tags": None,
                    "description": None,
                    "availability": availability,
                }
            except Exception as exc:
                logger.exception("Failed parsing a book card: %s", exc)

        next_link = soup.select_one("li.next a")
        next_url = urljoin(next_url, next_link.get("href")) if next_link and next_link.get("href") else None


def enrich_book(session: requests.Session, fetcher, logger, record: dict) -> dict:
    """Fetch a book detail page for category and description. Failures leave fields null."""
    soup = fetcher(session, record["source_url"], logger)
    if soup is None:
        return record
    try:
        breadcrumb = soup.select("ul.breadcrumb li a")
        # Home > Books > Category > Title
        if len(breadcrumb) >= 3:
            record["category"] = _text(breadcrumb[2]) or None
        desc = soup.select_one("#product_description + p")
        record["description"] = _text(desc) or None
    except Exception:
        logger.exception("Failed enriching book: %s", record.get("source_url"))
    return record
