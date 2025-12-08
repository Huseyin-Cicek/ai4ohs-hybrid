"""
Llama Learning Integration v4.0
--------------------------------

Bu modül:
- Long-term memory + code patterns + risk signals + ESS/6331 uyum problemlerini
  Llama.cpp modeline context olarak besler.
- LLM’den “learning summary” ve “refactor hints” alınır.
- Kod değişikliğine izin verilmez. Sadece öneri üretimi yapılır.
"""

import json

from agentic.memory.code_learning_engine import CodeLearningEngine
from agentic.memory.long_term_memory import LongTermMemory
from agentic.llama_learning_integration.llama_client import llama_cpp
from governance.audit_logger import log_event


class LlamaLearningIntegration:
    def __init__(self):
        self.mem = LongTermMemory()
        self.cle = CodeLearningEngine()

    def build_learning_prompt(self) -> str:
        patterns = self.cle.detect_patterns(self.cle.scan_codebase())
        risk_notes = self.mem.memory.get("risk_patterns", [])
        compliance_notes = self.mem.memory.get("compliance_issues", [])
        code_notes = self.mem.memory.get("code_patterns", [])

        prompt = f"""
You are the AI4OHS-HYBRID Learning Model.

Below is system-learned historical memory:

CODE PATTERNS:
{json.dumps(code_notes[-3:], indent=2)}

RISK PATTERNS:
{json.dumps(risk_notes[-3:], indent=2)}

COMPLIANCE ISSUES:
{json.dumps(compliance_notes[-3:], indent=2)}

TASK:
Generate:
- Learning summary
- Possible optimizations (non-destructive)
- Code architecture improvement hints
- Safety & compliance warnings
"""

        return prompt

    def run_learning_integration(self):
        prompt = self.build_learning_prompt()
        result = llama_cpp(prompt)

        # Hafızaya yaz
        self.mem.memory.setdefault("llm_learning_logs", [])
        self.mem.memory["llm_learning_logs"].append(result)
        self.mem.save()

        log_event("LLAMA_LEARNING", "Llama learning integration completed")
        return result
