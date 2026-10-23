"""
thresholds.py
-------------

All limits used by the project are kept in this one file.
If you want to change a rule, change it here only.

The numbers below are simple teaching values based on common drinking-water
and surface-water guidance. They are NOT an official legal standard.
"""

# ---------------------------------------------------------------------------
# Parameter information (used for labels, units and slider ranges in the app)
# ---------------------------------------------------------------------------

PARAMETERS = {
    "ph": {
        "label": "pH",
        "unit": "",
        "min_input": 0.0,
        "max_input": 14.0,
        "step": 0.1,
        "ideal_low": 6.5,
        "ideal_high": 8.5,
        "help": "How acidic or basic the water is. 7 is neutral.",
    },
    "tds": {
        "label": "TDS",
        "unit": "ppm",
        "min_input": 0.0,
        "max_input": 3000.0,
        "step": 1.0,
        "ideal_low": 0.0,
        "ideal_high": 500.0,
        "help": "Total Dissolved Solids: salts and minerals dissolved in water.",
    },
    "turbidity": {
        "label": "Turbidity",
        "unit": "NTU",
        "min_input": 0.0,
        "max_input": 200.0,
        "step": 0.1,
        "ideal_low": 0.0,
        "ideal_high": 5.0,
        "help": "How cloudy or muddy the water looks.",
    },
    "temperature": {
        "label": "Temperature",
        "unit": "C",
        "min_input": -5.0,
        "max_input": 60.0,
        "step": 0.1,
        "ideal_low": 10.0,
        "ideal_high": 25.0,
        "help": "Water temperature. Very warm water holds less oxygen.",
    },
}

# ---------------------------------------------------------------------------
# How important each parameter is in the final score (weights add up to 1.0)
# ---------------------------------------------------------------------------

WEIGHTS = {
    "ph": 0.25,
    "tds": 0.25,
    "turbidity": 0.35,
    "temperature": 0.15,
}

# ---------------------------------------------------------------------------
# Final classification bands (based on the overall 0-100 score)
# ---------------------------------------------------------------------------

GOOD_MIN_SCORE = 75.0      # overall score must be at least this for GOOD
CAUTION_MIN_SCORE = 50.0   # overall score must be at least this for CAUTION

# Safety rules that can pull the result down even if the average looks fine
MIN_PARAM_SCORE_FOR_GOOD = 60.0   # every parameter must be at least this for GOOD
CRITICAL_PARAM_SCORE = 25.0       # any parameter below this forces POOR

QUALITY_LEVELS = ("GOOD", "CAUTION", "POOR")

QUALITY_MEANING = {
    "GOOD": "Water looks healthy for its natural environment and is easy to treat.",
    "CAUTION": "Water has one or more problems. Treat it before any human contact or use.",
    "POOR": "Water is badly polluted. Do not drink, cook or bathe. Strong treatment is needed.",
}
