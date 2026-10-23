"""
storage.py
----------

Saves every analysed reading into a simple CSV file called `data/history.csv`.

A CSV file is used instead of a database so that beginners can open the file
in Excel, Google Sheets or any text editor.
"""

from __future__ import annotations

import csv
import io
import os
from typing import Dict, List

DATA_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
HISTORY_FILE = os.path.join(DATA_FOLDER, "history.csv")

COLUMNS = [
    "timestamp",
    "location",
    "source_type",
    "ph",
    "tds",
    "turbidity",
    "temperature",
    "ph_score",
    "tds_score",
    "turbidity_score",
    "temperature_score",
    "overall_score",
    "quality",
    "entry_mode",
]


def _ensure_file() -> None:
    """Create the data folder and the CSV header row if they do not exist."""
    os.makedirs(DATA_FOLDER, exist_ok=True)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS)
            writer.writeheader()


def row_from_analysis(analysis: Dict, entry_mode: str = "Manual") -> Dict[str, object]:
    """Flatten one analysis dictionary into a single CSV row."""
    return {
        "timestamp": analysis["timestamp"],
        "location": analysis["location"],
        "source_type": analysis["source_type"],
        "ph": analysis["values"]["ph"],
        "tds": analysis["values"]["tds"],
        "turbidity": analysis["values"]["turbidity"],
        "temperature": analysis["values"]["temperature"],
        "ph_score": analysis["scores"]["ph"],
        "tds_score": analysis["scores"]["tds"],
        "turbidity_score": analysis["scores"]["turbidity"],
        "temperature_score": analysis["scores"]["temperature"],
        "overall_score": analysis["overall_score"],
        "quality": analysis["quality"],
        "entry_mode": entry_mode,
    }


def append_reading(analysis: Dict, entry_mode: str = "Manual") -> None:
    """Add one analysed reading to the end of the history file."""
    _ensure_file()
    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writerow(row_from_analysis(analysis, entry_mode))


def append_many(analyses: List[Dict], entry_mode: str = "Simulated") -> None:
    """Add a list of analysed readings at once."""
    _ensure_file()
    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        for analysis in analyses:
            writer.writerow(row_from_analysis(analysis, entry_mode))


def load_history() -> List[Dict[str, str]]:
    """Read every saved row back as a list of dictionaries."""
    _ensure_file()
    with open(HISTORY_FILE, "r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def clear_history() -> None:
    """Delete all saved rows but keep the header."""
    os.makedirs(DATA_FOLDER, exist_ok=True)
    with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()


def history_to_csv(rows: List[Dict[str, object]] | None = None) -> str:
    """
    Turn the history into CSV text.
    Streamlit uses this text for the download button.
    """
    rows = rows if rows is not None else load_history()
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS)
    writer.writeheader()
    for row in rows:
        writer.writerow({column: row.get(column, "") for column in COLUMNS})
    return buffer.getvalue()
