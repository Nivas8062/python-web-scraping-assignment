from __future__ import annotations
from urllib.parse import urlparse


def validate_record(record: dict):
    errors = []
    if record.get("source") not in {"Books to Scrape", "Quotes to Scrape"}:
        errors.append("unrecognized_source")
    if not record.get("source_url"):
        errors.append("missing_source_url")
    else:
        parsed = urlparse(record["source_url"])
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append("invalid_source_url")
    if not record.get("name_or_title"):
        errors.append("missing_name_or_title")
    if record.get("price") is not None and not isinstance(record["price"], (int, float)):
        errors.append("non_numeric_price")
    if record.get("rating") is not None and record["rating"] not in range(1, 6):
        errors.append("rating_out_of_range")
    return (len(errors) == 0, errors)
