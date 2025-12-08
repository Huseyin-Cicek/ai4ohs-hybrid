"""
AI4OHS-HYBRID
Self-Planning Mode v1.0

Modülleri tarar → bağımlılık çıkarır → görevleri sınıflandırır →
otomatik task-graph oluşturur → Llama.cpp ile optimize eder →
Agentic Planner’a plan taslağı döner.
"""

import ast
import json
import os
from typing import Dict, List

from agentic.llama_learning_integration import llama_cpp
from governance.audit_logger import log_event

# ============================================================
# 1) MODULE DEPENDENCY EXTRACTOR
# ============================================================


class DependencyExtractor:
    def __init__(self, root="src"):
        self.root = root

    def scan(self) -> Dict[str, Dict]:
        mod_map = {}
        for dirpath, _, files in os.walk(self.root):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(dirpath, f)
                    mod_map[path] = self.extract(path)
        return mod_map

    def extract(self, path: str) -> Dict:
        try:
            with open(path, "r", encoding="utf-8") as fp:
                code = fp.read()
            tree = ast.parse(code)
        except Exception:
            return {"imports": [], "classes": [], "funcs": []}

        imports, classes, funcs = [], [], []

        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                for name in n.names:
                    imports.append(name.name)
            elif isinstance(n, ast.ImportFrom):
                imports.append(n.module or "")
            elif isinstance(n, ast.ClassDef):
                classes.append(n.name)
            elif isinstance(n, ast.FunctionDef):
                funcs.append(n.name)

        return {"imports": list(set(imports)), "classes": classes, "funcs": funcs}


# ============================================================
# 2) MODULE ROLE INFERENCE
# ============================================================


class RoleInferer:
    KEYWORDS = {
        "report": ["report", "dashboard", "annual", "quarter", "summary"],
        "incident": ["incident", "injury", "near miss", "faiss", "rca"],
        "risk": ["risk", "severity", "forecast", "hazard", "vector"],
        "compliance": ["ess", "6331", "iso", "cag", "policy"],
        "rag": ["retriever", "embedding", "rag", "chunk"],
        "agentic": ["agent", "planner", "task", "graph"],
        "zeus": ["listener", "startup", "optimizer"],
    }

    def infer_role(self, module_path: str, module_info: Dict) -> str:
        text = json.dumps(module_info).lower()

        for role, kws in self.KEYWORDS.items():
            if any(kw in text for kw in kws):
                return role

        return "general"


# ============================================================
# 3) TASK GRAPH DESIGNER
# ============================================================


class TaskGraphDesigner:
    def __init__(self):
        self.extractor = DependencyExtractor()
        self.role_infer = RoleInferer()

    def build_graph(self):
        modules = self.extractor.scan()

        # --- 1) Role inference ---
        roles = {}
        for path, info in modules.items():
            roles[path] = self.role_infer.infer_role(path, info)

        # --- 2) Dependency Graph ---
        graph = []
        for path, info in modules.items():
            graph.append({"module": path, "role": roles[path], "depends_on": info["imports"]})

        task_graph = {"modules": graph, "roles": roles}
        return task_graph

    # ========================================================
    # 4) Llama.cpp Optimization
    # ========================================================
    def optimize_graph(self, graph: Dict):
        prompt = f"""
Below is the dependency graph of AI4OHS-HYBRID modules:

{json.dumps(graph, indent=2)}

TASK:
- Analyze module roles and dependencies
- Suggest an optimized task ordering
- Identify recommended task groups (risk pipeline / reporting / compliance / rag)
- Suggest improvements WITHOUT modifying any code
"""

        result = llama_cpp(prompt)
        return result


# ============================================================
# 5) SELF-PLANNING INTERFACE
# ============================================================


class SelfPlanningMode:
    def __init__(self):
        self.designer = TaskGraphDesigner()

    def run(self):
        log_event("SELF_PLAN_START", "Self-planning mode initiated.")

        # 1) Build task graph
        graph = self.designer.build_graph()

        # 2) Ask Llama for optimized execution plan
        optimized = self.designer.optimize_graph(graph)

        plan = {"raw_graph": graph, "llm_plan_suggestion": optimized}

        log_event("SELF_PLAN_DONE", "Self-planning completed.", plan)
        return plan
