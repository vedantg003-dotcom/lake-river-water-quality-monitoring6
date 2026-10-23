"""
wq_core
=======

Core logic for the Automated Lake and River Water Quality Monitoring System.

This package is pure Python. It does not need Streamlit, so the same code can
be used by the web app, by unit tests, or by any other script.

Modules
-------
thresholds      : all safe/unsafe limits in one place
analysis        : turns raw readings into scores and a GOOD/CAUTION/POOR label
recommendations : suggests cleaning (treatment) methods and possible water uses
simulator       : creates fake but realistic readings for demos and testing
storage         : saves and loads the history CSV file
"""

from .analysis import analyse_reading, classify_overall, score_parameter
from .recommendations import recommend_treatments, suggest_uses
from .simulator import simulate_reading, simulate_many
from .storage import append_reading, load_history, clear_history, history_to_csv

__all__ = [
    "analyse_reading",
    "classify_overall",
    "score_parameter",
    "recommend_treatments",
    "suggest_uses",
    "simulate_reading",
    "simulate_many",
    "append_reading",
    "load_history",
    "clear_history",
    "history_to_csv",
]

__version__ = "1.0.0"
