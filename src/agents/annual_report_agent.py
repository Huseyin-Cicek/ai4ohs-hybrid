"""
AI4OHS-HYBRID
Annual Report Agent

Görev:
- Incident kayıtları + ESS/6331 checklist sonuçlarından yıllık OHS performans raporunu (Word + Excel) üretir.
- ai_ml.reporting.annual_ohs_report_generator modülünü çağırır.
"""

import json
import os
from typing import Any, Dict

from governance.audit_logger import log_event

INCIDENT_FILE = "data/analytics/incidents_annual.json"
ESS_FILE = "data/analytics/ess_6331_items.json"
OUT_DIR = "reports/annual"


def load_json_safe(path: str):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_annual_report_agent(context: Dict[str, Any] = None) -> Dict[str, str]:
    """
    context: ileride yıl/seçim vb. parametreler eklemek için kullanılabilir.
    Dönen:
      {"excel": "...", "word": "...", "kpi_png": "..."}
    """
    context = context or {}

    try:
        from ai_ml.reporting.annual_ohs_report_generator import generate_annual_ohs_report
    except ImportError as exc:  # pragma: no cover - environment guard
        raise RuntimeError("docx/openpyxl bağımlılıkları eksik: annual report üretilemedi.") from exc

    incidents = load_json_safe(INCIDENT_FILE)
    ess_items = load_json_safe(ESS_FILE)

    log_event(
        "ANNUAL_AGENT_START",
        "Annual report generation started.",
        {"incident_records": len(incidents), "ess_items": len(ess_items)},
    )

    result = generate_annual_ohs_report(
        incident_records=incidents, ess_items=ess_items, period_hours=None, out_dir=OUT_DIR
    )

    log_event("ANNUAL_AGENT_DONE", "Annual report generated.", result)
    return result
