from agentic.llama_learning_integration import llama_cpp
from governance.audit_logger import log_event
from typing import Any, Dict

"""
On-the-fly Model Selector v1.0
------------------------------

Amaç:
- Problem türüne göre en iyi ML modeli otomatik seçmek.
- Risk, incident classification, severity forecasting için farklı modeller önerir.
"""




class OnTheFlyModelSelector:

    def analyze_dataset(self, X, y):
        features = len(X[0]) if len(X) > 0 else 0
        samples = len(X)

        return {
            "num_samples": samples,
            "num_features": features,
            "problem_type": "regression" if isinstance(y[0], float) else "classification",
        }

    def select_model(self, X, y):
        info = self.analyze_dataset(X, y)

        prompt = f"""
Dataset info:
{info}

TASK:
- Determine best ML model among: LogisticRegression, RandomForest,
  MLP, XGBoost, NaiveBayes.
- Return JSON: {{"model": "...", "reason": "..."}}
"""
        result = llama_cpp(prompt)
        log_event("MODEL_SELECT", "Model selection completed", result)
        return result
        return result
