import json
from pathlib import Path

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "output" / "final_dataset.csv"
SUMMARY_FILE = BASE_DIR / "output" / "summary_report.json"


st.set_page_config(
    page_title="Python Web Scraping Pipeline",
    page_icon="🕷️",
    layout="wide",
)


@st.cache_data
def load_data():
    return pd.read_csv(DATA_FILE)


@st.cache_data
def load_summary():
    with open(SUMMARY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


st.title("🕷️ Python Web Scraping Pipeline")

st.write(
    "Multi-source web scraping pipeline with cleaning, "
    "validation, deduplication, and consolidated dataset generation."
)

try:
    df = load_data()
    summary = load_summary()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Final Records", summary["final_record_count"])
    col2.metric("Records Collected", summary["records_collected_total"])
    col3.metric("Duplicates Removed", summary["duplicates_detected_removed"])
    col4.metric("Rejected Records", summary["records_rejected_validation_or_processing"])

    st.divider()

    st.subheader("Records by Source")

    source_counts = df["source"].value_counts()

    st.bar_chart(source_counts)

    st.divider()

    st.subheader("Final Dataset")

    st.dataframe(
        df,
        use_container_width=True,
        height=500,
    )

    st.divider()

    st.subheader("Pipeline Summary")

    summary_table = pd.DataFrame(
        {
            "Metric": [
                "Books to Scrape",
                "Quotes to Scrape",
                "Total Records Collected",
                "Records After Cleaning",
                "Duplicates Removed",
                "Final Record Count",
                "Execution Time (seconds)",
            ],
            "Value": [
                summary["sources"].get("Books to Scrape", 0),
                summary["sources"].get("Quotes to Scrape", 0),
                summary["records_collected_total"],
                summary["records_after_cleaning"],
                summary["duplicates_detected_removed"],
                summary["final_record_count"],
                summary["execution_time_seconds"],
            ],
        }
    )

    st.table(summary_table)

except Exception as exc:
    st.error(f"Unable to load project data: {exc}")
