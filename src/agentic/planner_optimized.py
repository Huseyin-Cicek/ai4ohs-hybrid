"""
Agentic Planner — Llama.cpp Reasoning Path Optimizer
Ensures deterministic, short-step, safety/compliance-first planning.
"""

from governance.audit_logger import log_event


class ReasoningPathOptimizer:

    SHORT_STEP_LIMIT = 5  # llama.cpp optimum reasoning depth
    SAFETY_PRIORITIES = [
        "eliminate hazard",
        "engineering control",
        "administrative control",
        "PPE",
    ]

    def plan(self, task_description: str):
        log_event("PLAN_START", task_description)

        steps = [
            "Identify task type",
            "Identify regulatory scope (6331, ESS, ISO, OSHA)",
            "Determine if safety-critical",
            "Select RAG pipelines and retrievers",
            "Select agents to execute task",
        ]

        return steps[: self.SHORT_STEP_LIMIT]

    def reflect(self, output: str):
        """
        Validate reasoning according to safety & compliance constraints.
        """
        if "unsafe" in output.lower():
            return "Unsafe content detected; revise reasoning."
        if "unknown regulation" in output.lower():
            return "Invalid regulation reference; re-run CAG."
        return "OK"

    def correct(self, problem: str):
        if "unsafe" in problem.lower():
            return "Regenerate with stricter safety hierarchy."
        if "invalid regulation" in problem.lower():
            return "Re-check compliance mapping."
        return "Re-run reasoning with simplified plan."
