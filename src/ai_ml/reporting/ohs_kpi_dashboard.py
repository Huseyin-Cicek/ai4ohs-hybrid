"""
AI4OHS-HYBRID
OHS KPI Dashboard Generator (TRIR / LTIFR / Severity Index)

Girdi:
- incident_records: liste
  [
    {
      "date": "2025-10-01",
      "type": "LTI" | "MTI" | "FAI" | "NMI" | ...,
      "lost_days": 3,
      "work_hours": 120000   # ilgili dönem için toplam adam-saat (opsiyonel)
    },
    ...
  ]

- period_hours: dict (opsiyonel override)
  {
    "2025-10": 120000,
    "2025-11": 95000,
    ...
  }

Çıktı:
- hesaplanmış KPI sözlüğü
- opsiyonel matplotlib dashboard (PNG olarak kaydedilebilir)
"""

import datetime as dt
from collections import defaultdict
from typing import Dict, List, Optional


def _month_key(d: str) -> str:
    return d[:7]  # "YYYY-MM"


def compute_kpis(
    incident_records: List[Dict], period_hours: Optional[Dict[str, float]] = None
) -> Dict[str, Dict]:
    """
    KPI formülleri:
    TRIR  = (Toplam Kayıtlanabilir Olay × 1.000.000) / Toplam Adam-Saat
    LTIFR = (LTI sayısı × 1.000.000) / Toplam Adam-Saat
    SevIdx = (Toplam Kayıp Gün × 1.000) / Toplam Adam-Saat
    """

    if period_hours is None:
        period_hours = {}

    buckets = defaultdict(lambda: {"hours": 0.0, "total_recordable": 0, "lti": 0, "lost_days": 0.0})

    for rec in incident_records:
        date = rec.get("date")
        if not date:
            continue
        mkey = _month_key(date)

        if "work_hours" in rec:
            buckets[mkey]["hours"] += float(rec["work_hours"])

        itype = rec.get("type", "").upper()
        if itype in ["LTI", "MTI", "FAI", "NMI"]:  # ihtiyaç halinde genişletilebilir
            buckets[mkey]["total_recordable"] += 1

        if itype == "LTI":
            buckets[mkey]["lti"] += 1

        buckets[mkey]["lost_days"] += float(rec.get("lost_days", 0.0))

    # override saatleri kullan
    for period, hrs in period_hours.items():
        buckets[period]["hours"] = hrs

    kpis = {}
    for period, vals in sorted(buckets.items()):
        hrs = max(vals["hours"], 1.0)  # 0 bölmeyi engelle

        trir = (vals["total_recordable"] * 1_000_000) / hrs
        ltifr = (vals["lti"] * 1_000_000) / hrs
        sev_idx = (vals["lost_days"] * 1_000) / hrs

        kpis[period] = {
            "hours": hrs,
            "total_recordable": vals["total_recordable"],
            "lti": vals["lti"],
            "lost_days": vals["lost_days"],
            "TRIR": trir,
            "LTIFR": ltifr,
            "SeverityIndex": sev_idx,
        }

    return kpis


def plot_kpi_dashboard(kpis: Dict[str, Dict], filename: str = "ohs_kpi_dashboard.png"):
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - environment guard
        raise RuntimeError("matplotlib dependency missing for KPI plotting.") from exc

    periods = sorted(kpis.keys())
    trir = [kpis[p]["TRIR"] for p in periods]
    ltifr = [kpis[p]["LTIFR"] for p in periods]
    sev = [kpis[p]["SeverityIndex"] for p in periods]

    plt.figure(figsize=(12, 6))

    plt.plot(periods, trir, marker="o", label="TRIR")
    plt.plot(periods, ltifr, marker="s", label="LTIFR")
    plt.plot(periods, sev, marker="^", label="Severity Index")

    plt.xticks(rotation=45)
    plt.grid(True)
    plt.legend()
    plt.title("OHS KPI Dashboard (TRIR / LTIFR / Severity Index)")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

    return filename
