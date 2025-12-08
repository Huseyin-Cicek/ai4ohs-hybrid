"""
Strategic Control Panel Agent (SCPA) v1.0
-----------------------------------------

Bu ajan üç ileri sistem modülünü birleştirir:
1) Autonomous OHS Strategy Generator
2) RAG Evolution Engine
3) Self-Evolving System (Agent Topology Designer)

+ Human-in-the-loop compliance pipeline:
Her öneri sadece 'PROPOSAL' olarak üretilir ve kullanıcı onayı olmadan uygulanamaz.
"""

from typing import Any, Dict

from agentic.self_evolving_system import SelfEvolvingSystem
from agentic.strategy.autonomous_ohs_strategy_generator import AutonomousOHSStrategyGenerator
from genai.rag.rag_evolution_engine import RAGEvolutionEngine
from governance.approval_manager import ApprovalManager
from governance.audit_logger import log_event


class StrategicControlPanelAgent:
    def __init__(self):
        self.strategy = AutonomousOHSStrategyGenerator()
        self.evolver = SelfEvolvingSystem()
        self.rag_engine = RAGEvolutionEngine()
        self.approver = ApprovalManager()

    def run_all(self, horizon="12-month strategy") -> Dict[str, Any]:

        log_event("SCPA_START", "Strategic Control Panel Agent activated.")

        strat = self.strategy.generate_strategy(horizon)
        evolution = self.evolver.evolve()
        rag_next = self.rag_engine.evolve()

        proposal = {
            "ohs_strategy": strat,
            "agent_network_evolution": evolution,
            "rag_vNext": rag_next,
        }

        # PROPOSAL aşaması: approval olmadan uygulanamaz
        approval_id = self.approver.register_proposal(
            proposal_type="STRATEGIC_PACKAGE", proposal_content=proposal
        )

        log_event("SCPA_PROPOSAL", "Strategic package created", {"approval_id": approval_id})

        return {
            "proposal_id": approval_id,
            "proposal_package": proposal,
            "status": "AWAITING_APPROVAL",
        }
