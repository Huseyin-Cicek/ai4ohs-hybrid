"""
AI4OHS-HYBRID
Agentic Self-Evaluation Module (Answer Quality Scorer)

Amaç:
- Üretilen cevapları; yapı, mevzuat uyumu, güvenlik duyarlılığı ve netlik açısından puanlamak
- Llama.cpp reasoning + governance katmanı ile entegre basit bir skorlayıcı
"""

from typing import Dict, List

from governance.audit_logger import log_event


class SelfEvaluator:
    """
    Skor bileşenleri:
    - structure_score: required sections var mı (0–1)
    - compliance_score: compliance_mapping dolu mu, madde referansları var mı (0–1)
    - safety_score: safety kelimeleri, kontrol hiyerarşisi (0–1)
    - clarity_score: aşırı uzun / dağınık olmayan cevap (0–1)
    """

    REQUIRED_SECTIONS = [
        "Summary",
        "Findings",
        "Compliance Mapping",
        "Corrective Actions",
        "Preventive Actions",
        "Responsibilities",
        "Residual Risks",
    ]

    SAFETY_TERMS = [
        "engineering control",
        "administrative control",
        "PPE",
        "risk",
        "hazard",
        "control measure",
        "corrective action",
        "preventive action",
    ]

    def evaluate(self, answer_text: str, metadata: Dict) -> Dict[str, float]:
        structure_score = self._score_structure(answer_text)
        compliance_score = self._score_compliance(metadata.get("compliance_mapping"))
        safety_score = self._score_safety(answer_text)
        clarity_score = self._score_clarity(answer_text)

        overall = (structure_score + compliance_score + safety_score + clarity_score) / 4.0

        result = {
            "structure_score": structure_score,
            "compliance_score": compliance_score,
            "safety_score": safety_score,
            "clarity_score": clarity_score,
            "overall_score": overall,
        }

        log_event("SELF_EVAL", "Answer evaluated", result)
        return result

    def __init__(self, min_len=80, max_len=1500):
        self.min_len = min_len
        self.max_len = max_len

    def _score_structure(self, text: str) -> float:
        found = 0
        for sec in self.REQUIRED_SECTIONS:
            if sec.lower() in text.lower():
                found += 1
        return found / max(len(self.REQUIRED_SECTIONS), 1)

    def _score_compliance(self, compliance_mapping: List[Dict]) -> float:
        if not compliance_mapping:
            return 0.0
        refs = 0
        for c in compliance_mapping:
            if c.get("ref"):
                refs += 1
        return min(1.0, refs / max(len(compliance_mapping), 1))

    def _score_safety(self, text: str) -> float:
        text_l = text.lower()
        hits = sum(1 for term in self.SAFETY_TERMS if term in text_l)
        return min(1.0, hits / 5.0) if hits else 0.0

    def _score_clarity(self, text: str) -> float:
        length = len(text.split())
        if length < self.min_len:
            return 0.5
        if length > self.max_len:
            return 0.4
        return 1.0
