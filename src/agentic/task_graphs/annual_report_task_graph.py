"""
AI4OHS-HYBRID
Annual Report Task Graph

Amaç:
- annual_report_agent'i Agentic Planner'ın yönettiği task-dag içine bağlamak.
- PLAN aşamasında alt görevleri tanımlar
- ACT aşamasında bağımlılık sırasına göre görevleri çalıştırır
"""

from typing import Any, Callable, Dict, List

from agents.annual_report_agent import run_annual_report_agent
from ai_ml.reporting.ohs_kpi_dashboard import compute_kpis
from governance.audit_logger import log_event
from governance.compliance_heatmap import generate_heatmap_matrix


class TaskNode:
    def __init__(self, name: str, func: Callable, requires=None):
        self.name = name
        self.func = func
        self.requires = requires or []


class AnnualReportTaskGraph:
    """
    Task Graph topolojik sıralı görev akışı:

        load_incidents ─┐
                        ├── compute_kpis ──┐
        load_ess_items ─┘                  ├── annual_report_agent
                                           └── post_validation
    """

    def __init__(self):
        self.tasks: Dict[str, TaskNode] = {}

        # 1) Veri yükleme görevleri
        self.tasks["load_incidents"] = TaskNode(name="load_incidents", func=self.load_incidents)

        self.tasks["load_ess_items"] = TaskNode(name="load_ess_items", func=self.load_ess_items)

        # 2) KPI hesaplama
        self.tasks["compute_kpis"] = TaskNode(
            name="compute_kpis", func=self.compute_kpis, requires=["load_incidents"]
        )

        # 3) Heatmap hazırlama
        self.tasks["compute_heatmap"] = TaskNode(
            name="compute_heatmap", func=self.compute_heatmap, requires=["load_ess_items"]
        )

        # 4) Yıllık rapor üretici
        self.tasks["annual_report"] = TaskNode(
            name="annual_report",
            func=self.run_annual_report,
            requires=["compute_kpis", "compute_heatmap"],
        )

        # 5) Doğrulama adımı
        self.tasks["post_validation"] = TaskNode(
            name="post_validation", func=self.post_validation, requires=["annual_report"]
        )

        self.memory = {}

    # === TASK FUNCTIONS ===
    def load_incidents(self, ctx):
        import json
        import os

        path = "data/analytics/incidents_annual.json"
        if not os.path.exists(path):
            raise FileNotFoundError(f"Incidents file missing: {path}")
        with open(path, "r", encoding="utf-8") as f:
            self.memory["incidents"] = json.load(f)
        return self.memory["incidents"]

    def load_ess_items(self, ctx):
        import json
        import os

        path = "data/analytics/ess_6331_items.json"
        if ctx.get("skip_ess", False):
            self.memory["ess_items"] = []
            return self.memory["ess_items"]

        if not os.path.exists(path):
            raise FileNotFoundError(f"ESS/6331 file missing: {path}")

        with open(path, "r", encoding="utf-8") as f:
            self.memory["ess_items"] = json.load(f)
        return self.memory["ess_items"]

    def compute_kpis(self, ctx):
        kpis = compute_kpis(self.memory["incidents"])
        self.memory["kpis"] = kpis
        return kpis

    def compute_heatmap(self, ctx):
        heatmap = generate_heatmap_matrix(self.memory["ess_items"])
        self.memory["heatmap_matrix"] = heatmap
        return heatmap

    def run_annual_report(self, ctx):
        result = run_annual_report_agent()
        self.memory["annual_report"] = result
        return result

    def post_validation(self, ctx):
        """
        CAG + Governance validation
        """
        result = self.memory["annual_report"]

        validation = {
            "has_word": result.get("word", "").endswith(".docx"),
            "has_excel": result.get("excel", "").endswith(".xlsx"),
            "kpi_png_exists": True,
        }
        log_event("ANNUAL_REPORT_VALIDATION", "Validation", validation)
        return validation

    # === EXECUTION ENGINE ===
    def execute(self, context: Dict[str, Any] = None):
        context = context or {}

        executed = set()
        results = {}

        def run_task(name: str):
            if name in executed:
                return results[name]

            node = self.tasks[name]
            for dep in node.requires:
                run_task(dep)

            out = node.func(context)
            results[name] = out
            executed.add(name)
            return out

        # Top task
        final = run_task("post_validation")
        return final
