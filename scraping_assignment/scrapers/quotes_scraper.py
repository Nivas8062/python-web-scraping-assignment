from __future__ import annotations
from typing import Iterator
from urllib.parse import urljoin

BASE_URL = "https://quotes.toscrape.com/"
START_URL = BASE_URL


def _text(node) -> str:
    return " ".join(node.stripped_strings) if node else ""


def scrape_quotes(session, fetcher, logger) -> Iterator[dict]:
    next_url = START_URL
    seen_pages = set()
    while next_url and next_url not in seen_pages:
        seen_pages.add(next_url)
        soup = fetcher(session, next_url, logger)
        if soup is None:
            logger.error("Skipping failed quotes page: %s", next_url)
            break

        for quote in soup.select("div.quote"):
            try:
                text = _text(quote.select_one("span.text"))
                author_node = quote.select_one("small.author")
                author = _text(author_node) or None
                author_link = quote.select_one("span a[href*='/author/']")
                author_url = urljoin(next_url, author_link.get("href")) if author_link else None
                tags = [a.get_text(strip=True) for a in quote.select("div.tags a.tag")]
                yield {
                    "source": "Quotes to Scrape",
                    "source_url": author_url or next_url,
                    "name_or_title": text,
                    "category": None,
                    "price": None,
                    "rating": None,
                    "author": author,
                    "tags": ", ".join(tags) if tags else None,
                    "description": None,
                    "availability": None,
                    "author_url": author_url,
                }
            except Exception:
                logger.exception("Failed parsing quote on %s", next_url)

        next_link = soup.select_one("li.next a")
        next_url = urljoin(next_url, next_link.get("href")) if next_link and next_link.get("href") else None


def enrich_quote(session, fetcher, logger, record: dict) -> dict:
    if not record.get("author_url"):
        return record
    soup = fetcher(session, record["author_url"], logger)
    if soup is None:
        return record
    try:
        bio = soup.select_one(".author-description")
        record["description"] = _text(bio) or None
    except Exception:
        logger.exception("Failed enriching author: %s", record.get("author"))
    return record
