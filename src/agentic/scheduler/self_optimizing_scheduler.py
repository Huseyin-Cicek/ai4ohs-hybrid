"""
Self-Optimizing Task Scheduler v1.0
-----------------------------------

Amaç:
- Görev çalışma sürelerini ve başarı oranlarını öğrenir.
- Long-term memory’den performans skorlarını çeker.
- Görevleri yeniden sıralar.
- Llama.cpp ile 'priority recommendation' alır.
"""

import time
from typing import Dict, List

from agentic.llama_learning_integration import llama_cpp
from agentic.memory.long_term_memory import LongTermMemory
from governance.audit_logger import log_event


class SelfOptimizingTaskScheduler:
    def __init__(self):
        self.mem = LongTermMemory()

    def record_task_result(self, task_name: str, duration: float, success: bool):
        self.mem.memory.setdefault("task_performance", [])
        self.mem.memory["task_performance"].append(
            {"task": task_name, "duration": duration, "success": success, "timestamp": time.time()}
        )
        self.mem.save()

    def compute_task_priority(self, task_name: str) -> float:
        data = [x for x in self.mem.memory.get("task_performance", []) if x["task"] == task_name]

        if not data:
            return 1.0  # yeni görev—normal öncelik

        avg_duration = sum(d["duration"] for d in data) / len(data)
        fail_rate = 1.0 - (sum(1 for d in data if d["success"]) / len(data))

        # öncelik formülü:
        # daha kısa süre = yüksek öncelik
        # daha düşük fail-rate = yüksek öncelik
        priority = (1 / (avg_duration + 1)) * (1 - fail_rate + 0.1)
        return max(0.01, priority)

    def optimize_order(self, tasks: List[str]) -> List[str]:
        scored = [(t, self.compute_task_priority(t)) for t in tasks]

        # Llama.cpp’den "priority suggestion" alınır
        prompt = f"""
Tasks: {tasks}
Base priorities: {scored}

Suggest improved ordering. Return list only.
"""
        llama_out = llama_cpp(prompt)

        log_event("SELF_SCHEDULER", "Llama priority hint", {"raw": llama_out})

        # Basit fallback — priority descending:
        scored.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in scored]
        return [x[0] for x in scored]
