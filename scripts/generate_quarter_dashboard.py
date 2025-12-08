"""
AI4OHS-HYBRID
Generate Quarterly KPI Dashboard

Not:
- "data/analytics/incidents_annual.json" formatı örnek:
  [
    {"date": "2025-01-15", "type": "LTI", "lost_days": 3, "work_hours": 20000},
    ...
  ]
"""

import datetime as dt
import json
import os

from ai_ml.reporting.ohs_kpi_dashboard import compute_kpis, plot_kpi_dashboard
from governance.audit_logger import log_event

DATA_FILE = "data/analytics/incidents_annual.json"
OUT_DIR = "reports/quarterly"


def _parse_date(d: str) -> dt.date:
    return dt.datetime.strptime(d, "%Y-%m-%d").date()


def _last_quarter_period(today: dt.date) -> (dt.date, dt.date):
    # Basit: yıl 4 çeyreğe bölünür
    q = (today.month - 1) // 3 + 1
    last_q = q - 1
    year = today.year
    if last_q == 0:
        last_q = 4
        year -= 1

    start_month = (last_q - 1) * 3 + 1
    start = dt.date(year, start_month, 1)
    end_month = start_month + 2
    # ay sonu
    if end_month in [1, 3, 5, 7, 8, 10, 12]:
        end_day = 31
    elif end_month == 2:
        end_day = 29 if year % 4 == 0 else 28
    else:
        end_day = 30
    end = dt.date(year, end_month, end_day)
    return start, end


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        log_event("KPI_QTR_ERROR", f"Data file not found: {DATA_FILE}")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        incidents = json.load(f)

    today = dt.date.today()
    start, end = _last_quarter_period(today)

    filtered = []
    for rec in incidents:
        d = _parse_date(rec["date"])
        if start <= d <= end:
            filtered.append(rec)

    kpis = compute_kpis(filtered, period_hours=None)
    png_path = os.path.join(OUT_DIR, f"kpi_dashboard_{start}_{end}.png")
    plot_kpi_dashboard(kpis, png_path)

    log_event(
        "KPI_QTR_DONE",
        "Quarterly KPI dashboard generated.",
        {"start": str(start), "end": str(end), "file": png_path},
    )


if __name__ == "__main__":
    main()
