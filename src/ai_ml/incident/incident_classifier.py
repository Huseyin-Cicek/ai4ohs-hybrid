"""
AI4OHS-HYBRID
Unified OHS Incident Classification Model

Amaç:
- Olay açıklamalarını tekleştirilmiş bir sınıf setine (LTI, MTI, First Aid, Near Miss,
  Property Damage, Environmental Incident vb.) sınıflandırmak
- Tfidf + LogisticRegression pipeline (offline, hafif)
"""

import os

import joblib

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


DEFAULT_LABELS = [
    "LTI",  # Lost Time Injury
    "MTI",  # Medical Treatment Injury
    "FAI",  # First Aid Injury
    "NMI",  # Near Miss
    "PDI",  # Property Damage Incident
    "ENV",  # Environmental Incident
    "SAFE_OBS",  # Safe Observation
]


class IncidentClassifier:
    def __init__(self):
        self.pipe = None

    def init_pipeline(self):
        if not SKLEARN_AVAILABLE:
            raise RuntimeError("sklearn not available for incident classifier.")
        self.pipe = Pipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=20000, stop_words=None)),
                ("clf", LogisticRegression(max_iter=1000, multi_class="auto")),
            ]
        )

    def fit(self, texts, labels, test_size=0.2):
        if self.pipe is None:
            self.init_pipeline()

        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=test_size, random_state=42, stratify=labels
        )

        self.pipe.fit(X_train, y_train)
        y_pred = self.pipe.predict(X_test)
        report = classification_report(y_test, y_pred, labels=DEFAULT_LABELS, zero_division=0)
        return report

    def predict(self, text: str) -> str:
        if self.pipe is None:
            raise RuntimeError("Model not trained.")
        return self.pipe.predict([text])[0]

    def predict_proba(self, text: str):
        if self.pipe is None:
            raise RuntimeError("Model not trained.")
        if hasattr(self.pipe[-1], "predict_proba"):
            return self.pipe.predict_proba([text])[0]
        return None

    def save(self, path: str = "data/models/incident_classifier.pkl"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.pipe, path)

    def load(self, path: str = "data/models/incident_classifier.pkl"):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Incident classifier not found at {path}")
        self.pipe = joblib.load(path)
        return self.pipe
