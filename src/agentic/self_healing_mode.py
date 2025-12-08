"""
Self-Healing Mode v1.0
----------------------

Amaç:
- Sistem pipeline'larında oluşan bozuklukları tespit etmek.
- Güncel hata loglarına bakarak root-cause belirlemek.
- Llama.cpp’den 'healing' önerisi almak.
- Sadece öneri üretir; değişiklik yapmaz.
"""

import json
from typing import Dict, List

from agentic.llama_learning_integration import llama_cpp
from governance.audit_logger import log_event


class SelfHealingMode:
    ERROR_KEYWORDS = {
        "rag": ["faiss", "embedding", "retriever", "index"],
        "etl": ["convert", "markdown", "sanitize", "parse"],
        "agent": ["task", "graph", "planner", "loop"],
        "ml": ["fit", "model", "matrix", "vector", "value error"],
        "file": ["not found", "permission", "ios error"],
    }

    def detect_issues(self, logs: List[Dict]):
        issues = []
        for entry in logs:
            msg = str(entry.get("message")).lower()
            for category, kws in self.ERROR_KEYWORDS.items():
                if any(kw in msg for kw in kws):
                    issues.append({"category": category, "log": entry})
        return issues

    def propose_fix(self, issues: List[Dict]):
        prompt = f"""
Detected system issues:
{json.dumps(issues, indent=2)}

TASK:
- Identify root cause
- Suggest non-destructive healing steps
- Provide plan in JSON
"""
        return llama_cpp(prompt)

    def run(self, logs: List[Dict]):
        issues = self.detect_issues(logs)
        healing = self.propose_fix(issues)

        result = {"issues": issues, "healing_plan": healing}
        log_event("SELF_HEALING", "Healing analysis complete", result)
        return result
