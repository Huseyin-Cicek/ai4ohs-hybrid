"""
AI4OHS-HYBRID - Otonom Döngü Çalıştırıcısı

Adımlar:
1) SelfPlanningMode -> mevcut modüller için görev grafiği ve LLM önerisi
2) ACEExecutor (dry-run) -> sandbox refactor + pytest
3) SelfHealingMode -> son audit loglarından sorun tespiti ve iyileştirme önerisi
4) SelfEvolvingSystem -> ağ topolojisi önerisi
5) ApprovalManager -> paketlenen öneriyi onay kuyruğuna yaz
"""

import json
from pathlib import Path

from agentic.self_planning_mode import SelfPlanningMode
from agentic.auto_refactor.ace_executor import ACEExecutor
from agentic.self_healing_mode import SelfHealingMode
from agentic.self_evolving_system import SelfEvolvingSystem
from governance.approval_manager import ApprovalManager
from governance.audit_logger import LOG_FILE


def _load_recent_logs(limit: int = 100):
    path = Path(LOG_FILE)
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    logs = []
    for ln in lines:
        try:
            logs.append(json.loads(ln))
        except json.JSONDecodeError:
            continue
    return logs


def main():
    # 1) Self-planning
    planner = SelfPlanningMode()
    planning_result = planner.run()

    # 2) ACE dry-run (sandbox only)
    ace = ACEExecutor(project_root=".")
    ace_result = ace.run_full_refactor_cycle(dry_run=True)

    # 3) Self-healing önerisi (audit loglarından)
    logs = _load_recent_logs()
    healer = SelfHealingMode()
    healing_result = healer.run(logs)

    # 4) Topoloji / evrim önerisi
    evolver = SelfEvolvingSystem()
    evolution_result = evolver.evolve()

    proposal_package = {
        "planning": planning_result,
        "ace": ace_result,
        "healing": healing_result,
        "evolution": evolution_result,
    }

    approval = ApprovalManager()
    approval_id = approval.register_proposal(
        proposal_type="AUTONOMY_CYCLE", proposal_content=proposal_package
    )

    print(
        json.dumps(
            {
                "status": "SUBMITTED",
                "approval_id": approval_id,
                "ace_status": ace_result.get("status"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
