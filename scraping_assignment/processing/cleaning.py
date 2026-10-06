from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


def fix_mojibake(value: str) -> str:
    """Repair common UTF-8 text that was incorrectly decoded as Latin-1/CP1252."""
    if not value:
        return value

    # Only attempt repair when typical mojibake markers are present.
    markers = ("Ã", "Â", "â", "ð", "�")
    if not any(marker in value for marker in markers):
        return value

    try:
        repaired = value.encode("latin1").decode("utf-8")
        return repaired
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value


def clean_text(value):
    if value is None:
        return None

    value = str(value)

    # Repair common UTF-8/Latin-1 mojibake.
    value = fix_mojibake(value)

    # Remove Books to Scrape's "...more" marker.
    value = re.sub(r"\s*\.\.\.more\s*$", "", value, flags=re.IGNORECASE)

    # Normalize whitespace.
    value = re.sub(r"\s+", " ", value).strip()

    if not value:
        return None

    # Some Books to Scrape descriptions contain a shortened preview
    # followed immediately by the complete description.
    # Detect a repeated opening section and keep the complete version.
    normalized = value

    min_prefix_length = 60

    if len(normalized) > 150:
        prefix = normalized[:min_prefix_length]
        second_start = normalized.find(prefix, min_prefix_length + 1)

        if second_start != -1:
            value = normalized[second_start:]

    return value or None


def clean_price(value):
    if value is None or value == "":
        return None

    cleaned = re.sub(r"[^0-9.\-]", "", str(value))

    try:
        return float(Decimal(cleaned))
    except (InvalidOperation, ValueError):
        return None


def clean_rating(value):
    if value is None or value == "":
        return None

    if isinstance(value, str) and value.title() in RATING_MAP:
        return RATING_MAP[value.title()]

    try:
        number = int(float(value))
        return number if 1 <= number <= 5 else None
    except (TypeError, ValueError):
        return None


def normalize_tags(value):
    if value is None:
        return None

    if isinstance(value, list):
        values = value
    else:
        values = str(value).split(",")

    values = [
        clean_text(v).lower()
        for v in values
        if clean_text(v)
    ]

    return ", ".join(dict.fromkeys(values)) or None


def normalize_url(value):
    value = clean_text(value)

    if not value:
        return None

    parsed = urlparse(value)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None

    return value


def clean_record(record: dict, scraped_at: str) -> dict:
    result = dict(record)

    text_fields = [
        "source",
        "source_url",
        "name_or_title",
        "category",
        "author",
        "description",
        "availability",
        "author_url",
    ]

    for key in text_fields:
        if key in result:
            result[key] = clean_text(result[key])

    result["source_url"] = normalize_url(result.get("source_url"))

    if "author_url" in result:
        result["author_url"] = normalize_url(result.get("author_url"))

    result["price"] = clean_price(result.get("price"))
    result["rating"] = clean_rating(result.get("rating"))
    result["tags"] = normalize_tags(result.get("tags"))
    result["scraped_at"] = scraped_at

    return result