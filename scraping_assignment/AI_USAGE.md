# AI_USAGE.md

## Tool used

**Tool:** ChatGPT

## What AI was used for

- Translating the assignment requirements into a clean project structure.
- Designing the common standardized data model.
- Drafting Requests + BeautifulSoup scraping logic.
- Designing pagination using discovered `Next` links.
- Drafting cleaning, validation and duplicate-detection utilities.
- Adding retry, timeout, logging and per-source failure handling.
- Creating unit tests and documentation.
- Reviewing edge cases such as missing HTML elements, invalid values and duplicate whitespace/capitalization.

## Representative prompts

1. "Build a Python web scraping pipeline for Books to Scrape and Quotes to Scrape with pagination, cleaning, validation and deduplication."
2. "Add robust request retries, timeouts, logging and handling for individual page failures."
3. "Create a standardized schema for book and quote records and explain a defensible duplicate-detection strategy."

## AI-assisted parts

The initial project structure, scraper implementation, processing modules, tests and documentation were AI-assisted.

## Human review / changes

The implementation was reviewed against the assignment requirements. Source-specific selectors were kept isolated, missing fields are represented as null, and the duplicate key includes source/title/author rather than using exact raw-string comparison.

## Incorrect or incomplete AI suggestions discovered

No unverified production claims are intentionally included. The scraper is designed to fail safely when the public HTML structure differs from the expected structure and logs the failure instead of inventing data.

## Verification

Verification consists of:

- Running the unit tests with `pytest -q`.
- Running the complete scraper from a clean virtual environment.
- Checking that the final CSV contains the standardized columns.
- Checking that `summary_report.json` counts agree with the pipeline stages.
- Reviewing sample output records and log messages.
