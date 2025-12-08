"""
Code Refactor Agent
AI4OHS-HYBRID'in analiz edilen kod örüntülerine göre
performans, modülerlik, okunabilirlik, hız optimizasyonu önerileri üretir.
"""

from agentic.memory.code_learning_engine import CodeLearningEngine
from governance.audit_logger import log_event


class CodeRefactorAgent:

    def generate_refactor_plan(self):
        engine = CodeLearningEngine()
        patterns = engine.run_learning_cycle()

        plan = []
        for p in patterns.get("long_functions", []):
            plan.append(
                {
                    "issue": f"Function {p['function']} ({p['file']}) is too long.",
                    "suggestion": "Split into smaller sub-functional units.",
                }
            )

        for name, locs in patterns.get("duplicate_function_names", {}).items():
            plan.append(
                {
                    "issue": f"Duplicate function name '{name}' found in: {locs}",
                    "suggestion": "Unify logic into a shared utility module.",
                }
            )

        for p in patterns.get("complex_functions", []):
            plan.append(
                {
                    "issue": f"Function {p['function']} ({p['file']}) has deep nested loops.",
                    "suggestion": "Refactor by extracting nested blocks into helpers.",
                }
            )

        log_event("CODE_REFACTOR_PLAN", "Generated code optimization plan.", plan)
        return plan
        return plan
