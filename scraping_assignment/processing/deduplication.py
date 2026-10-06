from __future__ import annotations
import re
import unicodedata


def normalize_key(value):
    value = value or ""
    value = unicodedata.normalize("NFKC", str(value)).casefold()
    value = re.sub(r"\s+", " ", value).strip()
    return value


def deduplicate(records: list[dict]):
    """Deduplicate by source + normalized title/text + author.

    Source is part of the key because a book title and a quote can legitimately be identical.
    """
    seen = set()
    unique = []
    duplicates = []
    for record in records:
        key = (
            normalize_key(record.get("source")),
            normalize_key(record.get("name_or_title")),
            normalize_key(record.get("author")),
        )
        if key in seen:
            duplicates.append(record)
        else:
            seen.add(key)
            unique.append(record)
    return unique, duplicates
