"""
OHS Hazard Vectorizer — AI4OHS-HYBRID
Converts hazards into numerical feature vectors for ML models.
"""

import numpy as np

HAZARD_TYPES = [
    "fall_height",
    "machine",
    "electrical",
    "confined_space",
    "traffic",
    "chemical",
    "fire",
    "lifting",
    "excavation",
    "noise",
    "property_damage",
]

SEVERITY_WEIGHTS = {"low": 1, "medium": 2, "high": 3, "critical": 5}

PROBABILITY_SCALE = {"rare": 1, "unlikely": 2, "possible": 3, "likely": 4, "frequent": 5}


def hazard_vector(hazard_dict):
    """
    hazard_dict:
      {
        "type": "fall_height",
        "severity": "high",
        "probability": "possible",
        "controls": ["guardrail", "PPE"]
      }
    """

    vector = np.zeros(len(HAZARD_TYPES) + 3)

    # One-hot hazard type
    if hazard_dict["type"] in HAZARD_TYPES:
        idx = HAZARD_TYPES.index(hazard_dict["type"])
        vector[idx] = 1

    # Severity
    vector[len(HAZARD_TYPES)] = SEVERITY_WEIGHTS.get(hazard_dict["severity"], 1)

    # Probability
    vector[len(HAZARD_TYPES) + 1] = PROBABILITY_SCALE.get(hazard_dict["probability"], 1)

    # Number of controls applied
    vector[len(HAZARD_TYPES) + 2] = len(hazard_dict.get("controls", []))

    return vector


def risk_score(vector):
    """
    Simple risk model: severity × probability × (1 / controls+1)
    """
    sev = vector[len(HAZARD_TYPES)]
    prob = vector[len(HAZARD_TYPES) + 1]
    ctr = vector[len(HAZARD_TYPES) + 2]

    return sev * prob / (ctr + 1)
