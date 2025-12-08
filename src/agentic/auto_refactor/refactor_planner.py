"""
Refactor Planner — Llama.cpp JSON Patch Sürümü
----------------------------------------------

Görev:
- CodeLearningEngine ile kod kokularını / pattern'leri özetle
- Llama.cpp'ye JSON-only patch isteği gönder
- Çıktıyı güvenli şekilde parse et ve ACEExecutor'a "patches" listesi olarak dön
"""

import json

from agentic.llama_learning_integration.llama_client import llama_cpp_json
from agentic.memory.code_learning_engine import CodeLearningEngine
from governance.audit_logger import log_event

PATCH_INSTRUCTION_PROMPT = """
You are an expert Python refactoring assistant working on the AI4OHS-HYBRID project.

Your task:
Given the following analysis of code smells / patterns, generate a SMALL set of safe refactoring patches.

REQUIREMENTS:
- Output MUST be VALID JSON ONLY.
- DO NOT include any explanation outside JSON.
- Each patch fully rewrites ONE python file.
- Keep changes minimal and safe.
- Do not introduce new external dependencies.
- Do not change public APIs unless clearly necessary.

JSON SCHEMA:

[
  {
    "file": "agentic/auto_refactor/ace_executor.py",
    "new_code": "<FULL PYTHON FILE CONTENT>",
    "reason": "Short explanation of the improvement."
  }
]

Now, here is the analysis to base your patches on:
"""


class RefactorPlanner:
    def __init__(self):
        self.cle = CodeLearningEngine()

    def _parse_patches(self, data):
        """
        Llama'dan gelen JSON'u güvenli hale getir.
        """
        if not isinstance(data, list):
            log_event(
                "REFACTOR_PLAN_FORMAT_ERROR",
                "Llama JSON root is not a list.",
                {"type": str(type(data))},
            )
            return []

        patches = []
        for item in data:
            if not isinstance(item, dict):
                continue

            fpath = item.get("file")
            code = item.get("new_code")
            reason = item.get("reason", "")

            if not fpath or not code:
                continue

            patches.append(
                {
                    "file": fpath.replace("\\", "/").lstrip("/").replace("src/", ""),
                    "new_code": code,
                    "reason": reason,
                }
            )

        return patches

    def generate_refactor_plan(self):
        # 1) Mevcut kod tabanından pattern'leri çıkar
        patterns = self.cle.detect_patterns(self.cle.scan_codebase())

        analysis_json = json.dumps(patterns, indent=2)

        prompt = (
            PATCH_INSTRUCTION_PROMPT + "\n\n" + analysis_json + "\n\nReturn ONLY the JSON list."
        )

        try:
            raw_patches = llama_cpp_json(prompt, n_predict=2048)
        except Exception as e:
            log_event("REFACTOR_PLAN_LLM_ERROR", f"Llama JSON call failed: {e}", {})
            raw_patches = []

        patches = self._parse_patches(raw_patches)

        plan = {
            "patches": patches,
            "llm_raw": raw_patches,
            "pattern_summary": patterns,
        }

        log_event(
            "REFACTOR_PLAN",
            "Refactor plan generated via Llama.cpp.",
            {"patch_count": len(patches)},
        )

        return plan
