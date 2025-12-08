"""
AI4OHS-HYBRID
Unified Risk Pipeline

Bileşenler:
- IncidentClassifier: olay açıklamasından sınıf (LTI/MTI/NMI vs.)
- HazardVectorizer: hazard_dict -> numerical vector
- RiskForecaster: ML modeli (MLP/XGBoost) ile risk forecast

Kullanım:
- train_pipeline(...) ile eğit
- predict_pipeline(...) ile yeni kayıtlar için risk tahmini yap
"""

from typing import Dict, List, Tuple

import numpy as np

from ai_ml.incident.incident_classifier import IncidentClassifier
from ai_ml.risk_scoring.hazard_vectorizer import hazard_vector, risk_score
from ai_ml.risk_scoring.risk_forecast_model import RiskForecaster

LABEL_TO_HAZARD = {
    "LTI": {"type": "fall_height", "severity": "critical", "probability": "likely"},
    "MTI": {"type": "machine", "severity": "high", "probability": "possible"},
    "FAI": {"type": "machine", "severity": "medium", "probability": "possible"},
    "NMI": {"type": "fall_height", "severity": "medium", "probability": "possible"},
    "PDI": {"type": "property_damage", "severity": "medium", "probability": "possible"},
    "ENV": {"type": "chemical", "severity": "high", "probability": "possible"},
    "SAFE_OBS": {"type": "fall_height", "severity": "low", "probability": "rare"},
}


def _incident_to_vector(label: str, controls: List[str]) -> np.ndarray:
    base = LABEL_TO_HAZARD.get(
        label, {"type": "fall_height", "severity": "medium", "probability": "possible"}
    )
    hazard = dict(base)
    hazard["controls"] = controls
    return hazard_vector(hazard)


def prepare_training_data(records: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
    """
    records:
      [
        {
          "description": "...",
          "label": "LTI",
          "controls": ["guardrail", "PPE"],
          "target_risk": 12.5    # örneğin Severity Index veya custom risk score
        },
        ...
      ]
    """
    X, y = [], []
    for r in records:
        label = r.get("label") or "NMI"
        controls = r.get("controls") or []
        vec = _incident_to_vector(label, controls)
        X.append(vec)
        y.append(float(r.get("target_risk", risk_score(vec))))
    return np.array(X), np.array(y)


class UnifiedRiskPipeline:
    def __init__(self, model_type="xgboost"):
        self.incident_clf = IncidentClassifier()
        self.risk_model = RiskForecaster(model_type=model_type)

    def train_classifier(self, texts: List[str], labels: List[str]) -> str:
        report = self.incident_clf.fit(texts, labels)
        return report

    def train_forecaster(self, records: List[Dict]) -> float:
        X, y = prepare_training_data(records)
        score = self.risk_model.fit(X, y)
        return score

    def predict_risk(self, description: str, controls: List[str]) -> float:
        """
        description -> incident label -> hazard vector -> ML risk forecast
        """
        if self.incident_clf.pipe is None:
            raise RuntimeError(
                "Incident classifier not trained or loaded. Call train_classifier or load()."
            )
        if self.risk_model.model is None:
            raise RuntimeError(
                "Risk forecaster not trained or loaded. Call train_forecaster or load()."
            )

        label = self.incident_clf.predict(description)
        vec = _incident_to_vector(label, controls)
        pred = self.risk_model.predict(np.array([vec]))[0]
        return float(pred)
