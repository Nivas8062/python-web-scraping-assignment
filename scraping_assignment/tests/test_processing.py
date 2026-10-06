from processing.cleaning import clean_price, clean_rating, clean_text, normalize_tags
from processing.validation import validate_record
from processing.deduplication import deduplicate


def test_cleaning():
    assert clean_text("  A   Book  ") == "A Book"
    assert clean_price("£51.77") == 51.77
    assert clean_rating("Three") == 3
    assert normalize_tags("Life,  LOVE, life") == "life, love"


def test_validation():
    ok = {
        "source": "Books to Scrape", "source_url": "https://books.toscrape.com/x",
        "name_or_title": "Book", "price": 10.0, "rating": 5
    }
    assert validate_record(ok)[0]
    bad = dict(ok, rating=8)
    assert not validate_record(bad)[0]


def test_deduplication():
    rows = [
        {"source": "Books to Scrape", "name_or_title": "Example Book", "author": None},
        {"source": "Books to Scrape", "name_or_title": " example   book ", "author": None},
        {"source": "Quotes to Scrape", "name_or_title": "Example Book", "author": "A"},
    ]
    unique, duplicates = deduplicate(rows)
    assert len(unique) == 2
    assert len(duplicates) == 1
