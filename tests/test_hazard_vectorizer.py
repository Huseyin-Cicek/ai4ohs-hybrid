import numpy as np

from ai_ml.risk_scoring.hazard_vectorizer import HAZARD_TYPES, hazard_vector, risk_score


def test_risk_score_decreases_with_controls():
    base = {"type": HAZARD_TYPES[0], "severity": "high", "probability": "possible", "controls": []}
    v0 = hazard_vector(base)
    v1 = hazard_vector({**base, "controls": ["guardrail"]})
    assert risk_score(v1) < risk_score(v0)


def test_property_damage_type_is_encoded():
    hazard = {
        "type": "property_damage",
        "severity": "medium",
        "probability": "possible",
        "controls": [],
    }
    vec = hazard_vector(hazard)
    # property_damage tipi one-hot içinde işaretlenmeli
    assert vec[: len(HAZARD_TYPES)].sum() == 1
    assert vec[HAZARD_TYPES.index("property_damage")] == 1
