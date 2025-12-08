"""
AI4OHS-HYBRID
Risk Forecasting Model (MLP / XGBoost)

Amaç:
- OHS hazard & incident feature vektörlerinden kısa dönem risk forecast'i üretmek
- MLP (sklearn) veya XGBoost tabanlı modelleri desteklemek
- Offline, dosya tabanlı kaydet/yükle yapabilmek
"""

import os

import joblib
import numpy as np

try:
    from sklearn.metrics import r2_score
    from sklearn.model_selection import train_test_split
    from sklearn.neural_network import MLPRegressor

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from xgboost import XGBRegressor

    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False


class RiskForecaster:
    def __init__(self, model_type: str = "xgboost"):
        """
        model_type: "xgboost" veya "mlp"
        """
        self.model_type = model_type
        self.model = None

    def _init_model(self):
        if self.model_type == "xgboost" and XGBOOST_AVAILABLE:
            self.model = XGBRegressor(
                n_estimators=200,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                objective="reg:squarederror",
            )
        elif self.model_type == "mlp" and SKLEARN_AVAILABLE:
            self.model = MLPRegressor(
                hidden_layer_sizes=(64, 32), activation="relu", solver="adam", max_iter=500
            )
        else:
            raise RuntimeError("Required model library is not available.")

    def fit(self, X: np.ndarray, y: np.ndarray, test_size: float = 0.2):
        """
        X: feature matrix (n_samples, n_features)
        y: target risk scores (e.g., TRIR, LTIFR proxy, severity index)
        """
        if self.model is None:
            self._init_model()

        if SKLEARN_AVAILABLE and test_size > 0:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            self.model.fit(X_train, y_train)
            y_pred = self.model.predict(X_test)
            score = r2_score(y_test, y_pred)
            return score
        else:
            self.model.fit(X, y)
            return None

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("Model not trained yet.")
        return self.model.predict(X)

    def save(self, path: str = "data/models/risk_forecaster.pkl"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({"model_type": self.model_type, "model": self.model}, path)

    def load(self, path: str = "data/models/risk_forecaster.pkl"):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Risk model not found at {path}")
        obj = joblib.load(path)
        self.model_type = obj["model_type"]
        self.model = obj["model"]
        return self.model
