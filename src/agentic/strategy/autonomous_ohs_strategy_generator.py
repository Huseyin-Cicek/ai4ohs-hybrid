"""
Autonomous OHS Strategy Generator v1.0
--------------------------------------

Amaç:
- KPI, risk forecast, incident trendleri, ESS/6331 uyumu ve
  predictive optimization çıktılarından yıllık/çeyreklik OHS strateji planı taslağı oluşturmak.
- Strateji sadece öneri niteliğindedir; sistem ayarlarını değiştirmez.
"""

import json
from typing import Any, Dict, List

from agentic.llama_learning_integration import llama_cpp
from agentic.memory.long_term_memory import LongTermMemory
from governance.audit_logger import log_event


class AutonomousOHSStrategyGenerator:
    def __init__(self):
        self.mem = LongTermMemory()

    def _get_latest(self, key: str, default=None):
        items = self.mem.memory.get(key, [])
        if not items:
            return default
        return items[-1]

    def collect_context(self) -> Dict[str, Any]:
        """
        Hafızadan strateji için gerekli ana sinyalleri toplar.
        """
        kpi_trends = self._get_latest("kpi_annual_summary", {})
        risk_trend = self._get_latest("predicted_risk_trend", [])
        compliance = self._get_latest("ess_compliance_history", {})
        opt_preds = self._get_latest("optimization_predictions", {})
        incidents_meta = self._get_latest("incident_statistics", {})

        ctx = {
            "kpi_trends": kpi_trends,
            "risk_trend": risk_trend,
            "compliance": compliance,
            "optimization_predictions": opt_preds,
            "incident_statistics": incidents_meta,
        }
        return ctx

    def build_strategy_prompt(self, horizon: str, ctx: Dict[str, Any]) -> str:
        return f"""
You are AI4OHS-HYBRID Autonomous OHS Strategy Generator.

TIME HORIZON:
- {horizon} (e.g., 12-month strategy for TERRP)

INPUT SIGNALS:
- KPI trends: {json.dumps(ctx.get("kpi_trends"), indent=2)}
- Risk trend (forecast): {json.dumps(ctx.get("risk_trend"), indent=2)}
- ESS/6331 compliance: {json.dumps(ctx.get("compliance"), indent=2)}
- Optimization predictions: {json.dumps(ctx.get("optimization_predictions"), indent=2)}
- Incident statistics: {json.dumps(ctx.get("incident_statistics"), indent=2)}

TASK:
Generate a NON-DESTRUCTIVE OHS Strategy Plan including:
1) Executive Summary
2) Key Risk Themes
3) ESS/6331 Compliance Gaps
4) Strategic Objectives (SMART)
5) Priority Actions (hierarchy: eliminate → engineering → administrative → PPE)
6) Monitoring & KPIs (TRIR/LTIFR/Severity/leading indicators)
7) Capacity Building & Training Plan
8) Community & ESS10 Interface
9) Review & Continuous Improvement Cycle

Output in structured markdown.
"""

    def generate_strategy(self, horizon: str = "Next 12 months") -> Dict[str, Any]:
        ctx = self.collect_context()
        prompt = self.build_strategy_prompt(horizon, ctx)
        strategy_md = llama_cpp(prompt)

        result = {"horizon": horizon, "context_snapshot": ctx, "strategy_markdown": strategy_md}

        self.mem.memory.setdefault("ohs_strategy_history", [])
        self.mem.memory["ohs_strategy_history"].append(result)
        self.mem.save()

        log_event("OHS_STRATEGY", "Autonomous OHS strategy generated.", {"horizon": horizon})
        return result
        return result
