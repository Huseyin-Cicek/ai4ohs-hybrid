from agentic.llama_learning_integration import llama_cpp
from governance.audit_logger import log_event
from typing import Dict, List

"""
Auto-CoT Compression & Execution Planner v1.0
---------------------------------------------

Amaç:
- Llama.cpp için ideal reasoning chain uzunluğu üretmek.
- Planı kısaltmak, gereksiz adımları kaldırmak.
- 'short-step deterministic reasoning' modeline uygun hale getirmek.
"""




class AutoCoTOptimizer:
    MAX_STEPS = 6  # Llama.cpp için ideal CoT derinliği

    def compress(self, steps: List[str]) -> List[str]:
        if len(steps) <= self.MAX_STEPS:
            return steps

        # Llama’dan "which steps to remove" önerisi alınır
        prompt = f"""
Original plan steps:
{steps}

TASK:
- Choose essential steps only.
- Remove redundant items.
- Return compressed list <= {self.MAX_STEPS} items.
"""
        result = llama_cpp(prompt)
        log_event("COT_OPTIMIZER", "Compressed CoT result", result)

        # Fallback: sadece ilk MAX_STEPS adımı al
        return steps[: self.MAX_STEPS]
        return steps[: self.MAX_STEPS]
