"""
simulator.py
------------

Creates fake but realistic water readings.

This is how the project works WITHOUT any physical sensor.
The numbers come from Python's random module, not from real water.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Dict, List

# Typical ranges for different water situations.
# (low, high) for ph, tds, turbidity, temperature
SCENARIOS: Dict[str, Dict[str, tuple]] = {
    "Clean mountain lake": {
        "ph": (6.8, 7.8),
        "tds": (40, 220),
        "turbidity": (0.2, 2.0),
        "temperature": (11.0, 19.0),
    },
    "Normal river": {
        "ph": (6.5, 8.2),
        "tds": (180, 520),
        "turbidity": (2.0, 9.0),
        "temperature": (15.0, 26.0),
    },
    "River after heavy rain": {
        "ph": (6.2, 7.6),
        "tds": (250, 700),
        "turbidity": (25.0, 90.0),
        "temperature": (16.0, 27.0),
    },
    "Algae bloom lake": {
        "ph": (8.6, 9.6),
        "tds": (350, 800),
        "turbidity": (10.0, 35.0),
        "temperature": (26.0, 33.0),
    },
    "Industrial discharge": {
        "ph": (4.2, 5.9),
        "tds": (1100, 2400),
        "turbidity": (12.0, 60.0),
        "temperature": (24.0, 38.0),
    },
    "Sewage polluted canal": {
        "ph": (6.0, 7.2),
        "tds": (900, 1800),
        "turbidity": (40.0, 140.0),
        "temperature": (22.0, 32.0),
    },
}

DEFAULT_SITES = [
    "North Lake Inlet",
    "North Lake Centre",
    "River Bridge Point",
    "River Downstream",
    "Village Pond",
    "Canal Junction",
]


def simulate_reading(scenario: str | None = None,
                     location: str | None = None,
                     seed: int | None = None) -> Dict[str, object]:
    """
    Produce one simulated reading.

    Parameters
    ----------
    scenario : one of the keys in SCENARIOS, or None for a random scenario
    location : site name, or None for a random site
    seed     : fix the seed if you want the same numbers every time (testing)
    """
    rng = random.Random(seed)

    if scenario is None or scenario not in SCENARIOS:
        scenario = rng.choice(list(SCENARIOS.keys()))

    ranges = SCENARIOS[scenario]

    reading = {
        "scenario": scenario,
        "location": location or rng.choice(DEFAULT_SITES),
        "source_type": "Lake" if "lake" in scenario.lower() else "River",
        "ph": round(rng.uniform(*ranges["ph"]), 2),
        "tds": round(rng.uniform(*ranges["tds"]), 0),
        "turbidity": round(rng.uniform(*ranges["turbidity"]), 2),
        "temperature": round(rng.uniform(*ranges["temperature"]), 1),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return reading


def simulate_many(count: int = 20,
                  scenario: str | None = None,
                  minutes_between: int = 60,
                  seed: int | None = None) -> List[Dict[str, object]]:
    """
    Produce a list of readings that look like they were taken over time.

    Useful for filling the history table and the charts during a demo.
    """
    rng = random.Random(seed)
    now = datetime.now()
    readings: List[Dict[str, object]] = []

    for index in range(count):
        sub_seed = rng.randint(0, 1_000_000)
        item = simulate_reading(scenario=scenario, seed=sub_seed)
        moment = now - timedelta(minutes=minutes_between * (count - index - 1))
        item["timestamp"] = moment.strftime("%Y-%m-%d %H:%M:%S")
        readings.append(item)

    return readings
