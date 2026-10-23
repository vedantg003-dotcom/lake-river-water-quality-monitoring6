"""
recommendations.py
------------------

Two jobs:

1. recommend_treatments() : how can we clean this water?
2. suggest_uses()         : what can this water be used for, and what is unsafe?

Everything is rule based, so it is easy to read and easy to change.
"""

from __future__ import annotations

from typing import Dict, List


# ---------------------------------------------------------------------------
# 1. Cleaning / treatment methods
# ---------------------------------------------------------------------------

def recommend_treatments(analysis: Dict) -> List[Dict[str, str]]:
    """
    Build a list of treatment steps for one analysed sample.

    Each step is a dictionary:
        {"step": 1, "method": "...", "reason": "...", "cost": "Low"}
    """
    values = analysis["values"]
    ph = values["ph"]
    tds = values["tds"]
    turbidity = values["turbidity"]
    temperature = values["temperature"]
    quality = analysis["quality"]

    steps: List[Dict[str, str]] = []

    # --- Step group A: remove the visible dirt first -----------------------
    if turbidity > 25:
        steps.append({
            "method": "Settling tank (sedimentation)",
            "reason": "Water is very muddy. Let heavy particles fall to the bottom for 2-6 hours first.",
            "cost": "Low",
        })
        steps.append({
            "method": "Coagulation with alum or moringa seed powder",
            "reason": "Small clay particles stick together and sink, which makes filtering much easier.",
            "cost": "Low",
        })
    elif turbidity > 5:
        steps.append({
            "method": "Cloth or sand filtration",
            "reason": "Water is cloudy. A simple sand or multi-layer cloth filter removes most particles.",
            "cost": "Low",
        })
    elif turbidity > 1:
        steps.append({
            "method": "Fine cartridge filter (5 micron)",
            "reason": "Light cloudiness. A cheap cartridge filter will polish the water.",
            "cost": "Low",
        })

    # --- Step group B: fix the chemistry -----------------------------------
    if ph < 6.5:
        steps.append({
            "method": "Neutralise acidity (limestone / soda ash dosing)",
            "reason": f"pH {ph} is acidic. Acidic water corrodes pipes and can carry dissolved metals.",
            "cost": "Medium",
        })
    elif ph > 8.5:
        steps.append({
            "method": "Lower the pH (CO2 injection or food-grade acid dosing)",
            "reason": f"pH {ph} is too alkaline. High pH reduces how well chlorine disinfects.",
            "cost": "Medium",
        })

    if tds > 1200:
        steps.append({
            "method": "Reverse Osmosis (RO) or distillation",
            "reason": f"TDS {tds:.0f} ppm is very high. Only membrane treatment removes this much dissolved salt.",
            "cost": "High",
        })
    elif tds > 600:
        steps.append({
            "method": "Ion exchange or small RO unit",
            "reason": f"TDS {tds:.0f} ppm is above the comfortable taste limit.",
            "cost": "Medium",
        })
    elif tds > 300:
        steps.append({
            "method": "Activated carbon filter",
            "reason": "Moderate dissolved solids. Carbon improves taste, smell and removes organics.",
            "cost": "Low",
        })

    if temperature > 30:
        steps.append({
            "method": "Shade, aeration or a cooling pond",
            "reason": f"{temperature:.1f} C is warm. Warm water grows algae and bacteria faster.",
            "cost": "Low",
        })
    elif temperature < 5:
        steps.append({
            "method": "Allow water to warm before chemical dosing",
            "reason": "Very cold water slows down chlorine and other treatment chemicals.",
            "cost": "Low",
        })

    # --- Step group C: always disinfect at the end -------------------------
    if quality == "POOR":
        steps.append({
            "method": "Strong disinfection: boil for 3 minutes OR chlorinate then re-test",
            "reason": "Poor quality water must be assumed to carry harmful microbes.",
            "cost": "Low",
        })
    else:
        steps.append({
            "method": "Disinfection: boiling, chlorine tablets, UV lamp or SODIS (solar bottles)",
            "reason": "Disinfection is the final step before water is safe for people.",
            "cost": "Low",
        })

    if quality in ("CAUTION", "POOR"):
        steps.append({
            "method": "Laboratory confirmation test",
            "reason": "Send a sample to a certified lab for bacteria, nitrate and heavy-metal testing.",
            "cost": "Medium",
        })

    # Number the steps so the user can follow them in order.
    for index, step in enumerate(steps, start=1):
        step["step"] = str(index)

    return steps


# ---------------------------------------------------------------------------
# 2. Possible uses of the water
# ---------------------------------------------------------------------------

_USE_LIST = [
    "Drinking and cooking",
    "Bathing and washing clothes",
    "Crop irrigation",
    "Livestock drinking water",
    "Fish pond / aquatic life",
    "Cleaning, flushing and construction",
    "Industrial cooling",
]


def suggest_uses(analysis: Dict) -> List[Dict[str, str]]:
    """
    Decide, for each possible use, whether the water is:

        "SAFE"            - can be used as it is (with normal common sense)
        "AFTER TREATMENT" - only after the recommended cleaning steps
        "NOT SAFE"        - do not use for this purpose
    """
    values = analysis["values"]
    ph = values["ph"]
    tds = values["tds"]
    turbidity = values["turbidity"]
    temperature = values["temperature"]
    quality = analysis["quality"]

    results: List[Dict[str, str]] = []

    def add(use: str, verdict: str, reason: str) -> None:
        results.append({"use": use, "verdict": verdict, "reason": reason})

    # 1. Drinking and cooking -------------------------------------------------
    if quality == "GOOD" and turbidity <= 5 and tds <= 600 and 6.5 <= ph <= 8.5:
        add("Drinking and cooking", "AFTER TREATMENT",
            "Chemistry looks fine, but surface water must still be filtered and disinfected. "
            "This app cannot detect bacteria or chemicals.")
    elif quality == "CAUTION":
        add("Drinking and cooking", "AFTER TREATMENT",
            "Only after full treatment (filter + chemical correction + disinfection) "
            "and a laboratory test.")
    else:
        add("Drinking and cooking", "NOT SAFE",
            "Pollution level is too high for home treatment. Use another source.")

    # 2. Bathing and washing --------------------------------------------------
    if quality == "GOOD":
        add("Bathing and washing clothes", "SAFE",
            "Clear, balanced water is fine for washing. Avoid swallowing it.")
    elif quality == "CAUTION" and turbidity <= 25:
        add("Bathing and washing clothes", "AFTER TREATMENT",
            "Filter the water first. Keep it away from open wounds, eyes and the mouth.")
    else:
        add("Bathing and washing clothes", "NOT SAFE",
            "Skin, eye and stomach infections are likely with water this dirty.")

    # 3. Crop irrigation ------------------------------------------------------
    if tds <= 700 and 6.0 <= ph <= 8.5:
        add("Crop irrigation", "SAFE",
            "Salt level and pH suit most common crops.")
    elif tds <= 2000 and 5.5 <= ph <= 9.0:
        add("Crop irrigation", "AFTER TREATMENT",
            "Use only on salt-tolerant crops, water in the evening and flush the soil sometimes.")
    else:
        add("Crop irrigation", "NOT SAFE",
            "Salt or pH will damage the soil and reduce the harvest.")

    # 4. Livestock ------------------------------------------------------------
    if quality == "GOOD" and tds <= 1000:
        add("Livestock drinking water", "SAFE",
            "Acceptable for cattle, goats and poultry.")
    elif tds <= 3000 and quality != "POOR":
        add("Livestock drinking water", "AFTER TREATMENT",
            "Settle and filter the water first, and watch the animals for any illness.")
    else:
        add("Livestock drinking water", "NOT SAFE",
            "Water this poor can make animals sick.")

    # 5. Fish pond ------------------------------------------------------------
    if 6.5 <= ph <= 8.5 and turbidity <= 30 and 10 <= temperature <= 30:
        add("Fish pond / aquatic life", "SAFE",
            "pH, clarity and temperature are inside the comfortable range for most fish.")
    elif 6.0 <= ph <= 9.0 and turbidity <= 60:
        add("Fish pond / aquatic life", "AFTER TREATMENT",
            "Add aeration and control the pH before stocking fish.")
    else:
        add("Fish pond / aquatic life", "NOT SAFE",
            "These conditions would stress or kill most fish species.")

    # 6. Cleaning / flushing / construction -----------------------------------
    if turbidity <= 50 and quality != "POOR":
        add("Cleaning, flushing and construction", "SAFE",
            "Good enough for toilet flushing, floor washing and mixing concrete.")
    elif turbidity <= 100:
        add("Cleaning, flushing and construction", "AFTER TREATMENT",
            "Let the mud settle first so it does not block pipes.")
    else:
        add("Cleaning, flushing and construction", "NOT SAFE",
            "Extremely muddy water will clog pipes and pumps.")

    # 7. Industrial cooling ---------------------------------------------------
    if tds <= 800 and turbidity <= 10:
        add("Industrial cooling", "SAFE",
            "Low scaling and low fouling risk for cooling systems.")
    elif tds <= 1500:
        add("Industrial cooling", "AFTER TREATMENT",
            "Needs anti-scale dosing and regular blow-down.")
    else:
        add("Industrial cooling", "NOT SAFE",
            "High TDS will quickly build scale inside the equipment.")

    return results


# ---------------------------------------------------------------------------
# 3. Safety warnings shown with every result
# ---------------------------------------------------------------------------

GENERAL_WARNINGS = [
    "This app only looks at pH, TDS, turbidity and temperature.",
    "It cannot detect bacteria, viruses, nitrate, fluoride, pesticides or heavy metals.",
    "Readings are typed in by hand or simulated, so they are not measured from real water.",
    "Never decide that water is drinkable using this app alone. Always confirm with a certified laboratory.",
    "When in doubt, boil the water for at least 3 minutes before drinking.",
]
