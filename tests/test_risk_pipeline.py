import pytest

from ai_ml.risk_scoring.risk_pipeline import UnifiedRiskPipeline


def test_predict_risk_requires_trained_models():
    rp = UnifiedRiskPipeline()
    with pytest.raises(RuntimeError):
        rp.predict_risk("test incident", [])
