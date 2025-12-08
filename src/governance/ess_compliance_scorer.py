"""
AI4OHS-HYBRID
ESS Compliance Scoring Engine

Amaç:
- ESS1–ESS10 için uyum skorlarını hesaplamak
- Her ESS için checklist sonuçlarından (E/H/K vb.) yüzde uyum üretmek
- Ağırlıklı genel ESS uyum skoru (ESS2, ESS4, ESS10 daha yüksek ağırlık)
"""

ESS_WEIGHTS = {
    "ESS1": 1.0,
    "ESS2": 1.5,
    "ESS3": 1.0,
    "ESS4": 1.5,
    "ESS5": 1.0,
    "ESS6": 1.0,
    "ESS7": 1.0,
    "ESS8": 1.0,
    "ESS9": 1.0,
    "ESS10": 1.5,
}


def ess_score_from_items(items):
    """
    items: [
      {"ess": "ESS2", "status": "E"},
      {"ess": "ESS2", "status": "H"},
      ...
    ]
    status:
      E: Uyumlu (1.0)
      K: Kısmen (0.5)
      H: Uyumlu değil (0.0)
    """
    scores = {}
    counts = {}

    def status_value(s):
        s = (s or "").upper()
        if s == "E":
            return 1.0
        if s == "K":
            return 0.5
        return 0.0

    for it in items:
        ess = it["ess"]
        val = status_value(it.get("status", "H"))
        scores[ess] = scores.get(ess, 0.0) + val
        counts[ess] = counts.get(ess, 0) + 1

    ess_percentages = {}
    for ess, total in scores.items():
        ess_percentages[ess] = (total / max(counts[ess], 1)) * 100.0

    # Weighted overall score
    overall_num = 0.0
    overall_den = 0.0
    for ess, pct in ess_percentages.items():
        w = ESS_WEIGHTS.get(ess, 1.0)
        overall_num += pct * w
        overall_den += w

    overall = overall_num / overall_den if overall_den > 0 else 0.0

    return {"ess_details": ess_percentages, "overall_score": overall}
