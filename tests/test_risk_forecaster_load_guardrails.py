import pytest

from ai_ml.risk_scoring.risk_forecast_model import RiskForecaster


def test_load_missing_model():
    rf = RiskForecaster()
    with pytest.raises(FileNotFoundError):
        rf.load("nope.pkl")
