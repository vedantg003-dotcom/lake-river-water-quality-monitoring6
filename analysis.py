"""
analysis.py
-----------

Turns four raw readings (pH, TDS, turbidity, temperature) into:

1. a 0-100 score for each parameter,
2. a short status word for each parameter,
3. one overall 0-100 score,
4. one final label: GOOD, CAUTION or POOR.

A higher score always means better water.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict

from .thresholds import (
    CAUTION_MIN_SCORE,
    CRITICAL_PARAM_SCORE,
    GOOD_MIN_SCORE,
    MIN_PARAM_SCORE_FOR_GOOD,
    PARAMETERS,
    QUALITY_MEANING,
    WEIGHTS,
)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    """Keep a number inside the low..high range."""
    return max(low, min(high, value))


def _ramp(value: float, start: float, end: float,
          score_at_start: float, score_at_end: float) -> float:
    """
    Draw a straight line between two points and read the score off it.

    Example: _ramp(450, 300, 600, 100, 80) -> 90
    """
    if end == start:
        return score_at_end
    fraction = (value - start) / (end - start)
    return score_at_start + fraction * (score_at_end - score_at_start)


# ---------------------------------------------------------------------------
# Score for each single parameter
# ---------------------------------------------------------------------------

def _score_ph(ph: float) -> float:
    """6.5 to 8.5 is the safe window. Score drops as we move away from it."""
    if 6.5 <= ph <= 8.5:
        return 100.0
    distance = (6.5 - ph) if ph < 6.5 else (ph - 8.5)
    return _clamp(100.0 - distance * 42.0)


def _score_tds(tds: float) -> float:
    """Low TDS is good. Very high TDS means salty or polluted water."""
    if tds <= 300:
        return 100.0
    if tds <= 600:
        return _ramp(tds, 300, 600, 100, 80)
    if tds <= 900:
        return _ramp(tds, 600, 900, 80, 60)
    if tds <= 1200:
        return _ramp(tds, 900, 1200, 60, 35)
    if tds <= 2000:
        return _ramp(tds, 1200, 2000, 35, 0)
    return 0.0


def _score_turbidity(ntu: float) -> float:
    """Clear water scores high. Muddy water scores low."""
    if ntu <= 1:
        return 100.0
    if ntu <= 5:
        return _ramp(ntu, 1, 5, 100, 78)
    if ntu <= 10:
        return _ramp(ntu, 5, 10, 78, 55)
    if ntu <= 50:
        return _ramp(ntu, 10, 50, 55, 15)
    if ntu <= 100:
        return _ramp(ntu, 50, 100, 15, 0)
    return 0.0


def _score_temperature(celsius: float) -> float:
    """10 C to 25 C is a healthy range for most lakes and rivers."""
    if 10.0 <= celsius <= 25.0:
        return 100.0
    distance = (10.0 - celsius) if celsius < 10.0 else (celsius - 25.0)
    return _clamp(100.0 - distance * 5.0)


_SCORERS = {
    "ph": _score_ph,
    "tds": _score_tds,
    "turbidity": _score_turbidity,
    "temperature": _score_temperature,
}


def score_parameter(name: str, value: float) -> float:
    """Public helper: score one parameter by name."""
    key = name.lower()
    if key not in _SCORERS:
        raise ValueError(f"Unknown parameter: {name}")
    return round(_SCORERS[key](float(value)), 1)


# ---------------------------------------------------------------------------
# Status word and plain-English note for each parameter
# ---------------------------------------------------------------------------

def _status_from_score(score: float) -> str:
    if score >= 75:
        return "GOOD"
    if score >= 50:
        return "CAUTION"
    return "POOR"


def _note_for(name: str, value: float, score: float) -> str:
    """A short sentence that explains the reading in simple words."""
    if name == "ph":
        if value < 6.5:
            return "Water is acidic. Acid water can dissolve metals from pipes and rocks."
        if value > 8.5:
            return "Water is alkaline (basic). It can taste bitter and leave scale."
        return "pH is inside the safe 6.5 to 8.5 window."
    if name == "tds":
        if value <= 300:
            return "Very few dissolved solids. This is clean, soft water."
        if value <= 600:
            return "Normal amount of dissolved minerals."
        if value <= 1200:
            return "High dissolved solids. Water may taste salty or metallic."
        return "Very high dissolved solids. Likely salt, sewage or industrial pollution."
    if name == "turbidity":
        if value <= 1:
            return "Water is clear."
        if value <= 5:
            return "Slightly cloudy, still acceptable after basic filtering."
        if value <= 10:
            return "Cloudy water. Mud or algae is suspended in it."
        return "Very muddy water. Disinfection will not work well until it is filtered."
    if name == "temperature":
        if value < 10:
            return "Cold water. Treatment chemicals and bacteria work more slowly."
        if value > 25:
            return "Warm water. Warm water holds less oxygen and grows more algae."
        return "Temperature is in the healthy range."
    return ""


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def classify_overall(scores: Dict[str, float]) -> Dict[str, object]:
    """
    Combine the four parameter scores into one overall score and label.

    Rules
    -----
    * overall score = weighted average of the four scores
    * any parameter below CRITICAL_PARAM_SCORE  -> POOR (safety override)
    * GOOD needs a high average AND no weak parameter
    """
    overall = sum(scores[key] * WEIGHTS[key] for key in WEIGHTS)
    overall = round(_clamp(overall), 1)

    weakest_name = min(scores, key=lambda k: scores[k])
    weakest_score = scores[weakest_name]

    override_reason = ""
    if weakest_score < CRITICAL_PARAM_SCORE:
        label = "POOR"
        override_reason = (
            f"{PARAMETERS[weakest_name]['label']} is at a dangerous level, "
            "so the whole sample is marked POOR."
        )
    elif overall >= GOOD_MIN_SCORE and weakest_score >= MIN_PARAM_SCORE_FOR_GOOD:
        label = "GOOD"
    elif overall >= CAUTION_MIN_SCORE:
        label = "CAUTION"
    elif overall >= GOOD_MIN_SCORE:
        # Average is high but one parameter is weak -> not good enough.
        label = "CAUTION"
        override_reason = (
            f"The average is high, but {PARAMETERS[weakest_name]['label']} "
            "is too weak for a GOOD result."
        )
    else:
        label = "POOR"

    # Average high + weak parameter case when overall >= GOOD_MIN_SCORE
    if label == "CAUTION" and overall >= GOOD_MIN_SCORE and not override_reason:
        override_reason = (
            f"The average is high, but {PARAMETERS[weakest_name]['label']} "
            "is too weak for a GOOD result."
        )

    return {
        "overall_score": overall,
        "quality": label,
        "meaning": QUALITY_MEANING[label],
        "weakest_parameter": weakest_name,
        "weakest_score": weakest_score,
        "override_reason": override_reason,
    }


def analyse_reading(ph: float, tds: float, turbidity: float, temperature: float,
                    location: str = "Unknown site",
                    source_type: str = "Lake",
                    timestamp: str | None = None) -> Dict[str, object]:
    """
    Analyse one water sample.

    Returns a dictionary that the Streamlit app can display directly.
    """
    values = {
        "ph": float(ph),
        "tds": float(tds),
        "turbidity": float(turbidity),
        "temperature": float(temperature),
    }

    scores = {key: score_parameter(key, value) for key, value in values.items()}

    details = {}
    for key, value in values.items():
        details[key] = {
            "label": PARAMETERS[key]["label"],
            "unit": PARAMETERS[key]["unit"],
            "value": value,
            "score": scores[key],
            "status": _status_from_score(scores[key]),
            "ideal_low": PARAMETERS[key]["ideal_low"],
            "ideal_high": PARAMETERS[key]["ideal_high"],
            "note": _note_for(key, value, scores[key]),
        }

    summary = classify_overall(scores)

    return {
        "timestamp": timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "location": location,
        "source_type": source_type,
        "values": values,
        "scores": scores,
        "details": details,
        **summary,
    }
