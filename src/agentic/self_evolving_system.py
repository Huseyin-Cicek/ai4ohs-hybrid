"""
Full Self-Evolving System (Non-Destructive) v1.0
------------------------------------------------

Amaç:
- Agent ağının (annual_report_agent, risk_pipeline, scheduler, self-healing, vb.)
  performansını izlemek,
- Kendi kendine 'ideal yapı' için öneri üretmek,
- Hiçbir ajanı otomatik açıp/kapatmadan, sadece öneri/pattern çıkarmak.
"""

import json
from typing import Any, Dict, List

from agentic.llama_learning_integration import llama_cpp
from agentic.memory.long_term_memory import LongTermMemory
from governance.audit_logger import log_event


class SelfEvolvingSystem:
    def __init__(self):
        self.mem = LongTermMemory()

    def collect_agent_metrics(self) -> List[Dict[str, Any]]:
        """
        agent_metrics:
          [
            {"agent": "annual_report_agent", "runs": 5, "avg_duration": 12.3, "success_rate": 0.9},
            ...
          ]
        """
        return self.mem.memory.get("agent_metrics", [])

    def collect_task_performance(self) -> List[Dict[str, Any]]:
        return self.mem.memory.get("task_performance", [])

    def build_topology_prompt(self, goal: str, agents: List[Dict], tasks: List[Dict]) -> str:
        return f"""
You are the AI4OHS-HYBRID Self-Evolving System.

HIGH-LEVEL GOAL:
- {goal}

CURRENT AGENT METRICS:
{json.dumps(agents, indent=2)}

TASK PERFORMANCE:
{json.dumps(tasks[-30:], indent=2)}

TASK:
- Propose an optimized agent network topology:
  - Which agents should be primary, supporting, or on-demand
  - How tasks should flow between agents (high-level graph)
  - How to improve robustness, latency, and reliability
- DO NOT enable/disable agents; only suggest topology and configuration.
- Return JSON with:
  - nodes (agents)
  - edges (directed flows)
  - annotations (rationale)
"""

    def evolve(
        self, goal: str = "Robust, low-latency, safety-first OHS intelligence"
    ) -> Dict[str, Any]:
        agents = self.collect_agent_metrics()
        tasks = self.collect_task_performance()
        prompt = self.build_topology_prompt(goal, agents, tasks)
        suggestion = llama_cpp(prompt)

        result = {
            "goal": goal,
            "agent_metrics": agents,
            "task_performance": tasks[-30:],
            "topology_suggestion": suggestion,
        }

        self.mem.memory.setdefault("self_evolution_history", [])
        self.mem.memory["self_evolution_history"].append(result)
        self.mem.save()

        log_event("SELF_EVOLVE", "Self-evolution suggestion generated.", {"goal": goal})
        return result
