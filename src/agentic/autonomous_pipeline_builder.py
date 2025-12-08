"""
Full Autonomous Pipeline Builder v1.0
-------------------------------------

Amaç:
- Kullanıcının amacına göre baştan pipeline tasarlamak.
- Görev, modül, bağımlılık, RAG ayarları, ML ihtiyaçları ve
  yürütülebilir task graph oluşturmak.
"""

import json
from typing import Any, Dict, List

from agentic.llama_learning_integration import llama_cpp
from agentic.self_planning_mode import DependencyExtractor, RoleInferer
from genai.rag.adaptive_pipeline_designer import AdaptiveRAGPipelineDesigner
from governance.audit_logger import log_event


class AutonomousPipelineBuilder:

    def __init__(self):
        self.extractor = DependencyExtractor()
        self.roles = RoleInferer()
        self.rag_designer = AdaptiveRAGPipelineDesigner()

    # --------------------------------------------------------------
    # 1) Goal understanding + initial LLM analysis
    # --------------------------------------------------------------
    def interpret_goal(self, goal: str) -> Dict:
        prompt = f"""
You are AI4OHS Autonomous Pipeline Builder.

USER GOAL:
{goal}

TASK:
- Identify required functions (e.g., KPI analysis, incident analysis, compliance check)
- Identify required data sources
- Identify required models (ML / RAG / agents)
- Return JSON only.
"""
        raw = llama_cpp(prompt)
        return {"goal_analysis": raw}

    # --------------------------------------------------------------
    # 2) Select modules automatically
    # --------------------------------------------------------------
    def select_required_modules(self, goal: str) -> List[str]:
        all_mods = self.extractor.scan()
        selected = []

        text = goal.lower()

        mapping = {
            "report": "reporting",
            "kpi": "reporting",
            "ess": "compliance",
            "incident": "incident",
            "risk": "risk",
            "rag": "rag",
            "optimize": "agentic",
            "task": "agentic",
        }

        for path, info in all_mods.items():
            role = self.roles.infer_role(path, info)
            if any(k in text for k in mapping.keys()) and role in mapping.values():
                selected.append(path)

        return selected

    # --------------------------------------------------------------
    # 3) Build dependency graph for selected modules
    # --------------------------------------------------------------
    def build_dependency_graph(self, modules: List[str]) -> List[Dict]:
        mod_info = self.extractor.scan()
        graph = []
        for m in modules:
            graph.append({"module": m, "imports": mod_info[m]["imports"]})
        return graph

    # --------------------------------------------------------------
    # 4) Adaptive RAG configuration
    # --------------------------------------------------------------
    def build_rag_config(self):
        return self.rag_designer.propose_new_chunking_rules()

    # --------------------------------------------------------------
    # 5) Generate runnable pipeline (task graph)
    # --------------------------------------------------------------
    def build_pipeline(self, goal: str, modules: List[str]) -> Dict:
        prompt = f"""
Goal: {goal}

Modules: {modules}

TASK:
- Create an execution pipeline.
- Define tasks, dependencies, triggers, outputs.
- Include RAG, ML, Compliance if relevant.
- DO NOT modify code, only describe a runnable plan.

Return JSON.
"""
        plan = llama_cpp(prompt)
        return {"pipeline_plan": plan}

    # --------------------------------------------------------------
    # 6) Main runner
    # --------------------------------------------------------------
    def run(self, goal: str):
        log_event("PIPELINE_BUILDER_START", "Pipeline building started", {"goal": goal})

        goal_info = self.interpret_goal(goal)
        modules = self.select_required_modules(goal)
        deps = self.build_dependency_graph(modules)
        rag_cfg = self.build_rag_config()
        pipeline = self.build_pipeline(goal, modules)

        result = {
            "goal_info": goal_info,
            "selected_modules": modules,
            "dependencies": deps,
            "rag_config": rag_cfg,
            "pipeline": pipeline,
        }

        log_event("PIPELINE_BUILDER_DONE", "Pipeline building completed", result)
        return result
        return result
