"""
Human-in-the-loop Approval Manager v1.0
---------------------------------------

Amaç:
- Autonomous modüllerin ürettiği tüm önerileri 'proposal' olarak kaydeder.
- Onay olmadan hiçbir pipeline, RAG ayarı veya strateji uygulanamaz.
- Tüm onay/ret işlemleri audit log'a kaydedilir.
"""

import time
import uuid
from typing import Any, Dict

from agentic.memory.long_term_memory import LongTermMemory
from governance.audit_logger import log_event


class ApprovalManager:
    def __init__(self):
        self.mem = LongTermMemory()
        self.mem.memory.setdefault("approval_queue", [])
        self.mem.save()

    def register_proposal(self, proposal_type: str, proposal_content: Any) -> str:
        pid = str(uuid.uuid4())
        entry = {
            "id": pid,
            "timestamp": time.time(),
            "type": proposal_type,
            "content": proposal_content,
            "status": "PENDING",
            "approved_by": None,
            "approved_timestamp": None,
        }
        self.mem.memory["approval_queue"].append(entry)
        self.mem.save()
        return pid

    def list_pending(self):
        return [p for p in self.mem.memory.get("approval_queue", []) if p["status"] == "PENDING"]

    def approve(self, proposal_id: str, user: str = "admin"):
        for p in self.mem.memory["approval_queue"]:
            if p["id"] == proposal_id:
                p["status"] = "APPROVED"
                p["approved_by"] = user
                p["approved_timestamp"] = time.time()
                self.mem.save()
                log_event("APPROVAL", "Proposal approved", {"id": proposal_id})
                return p
        return None

    def reject(self, proposal_id: str, user: str = "admin"):
        for p in self.mem.memory["approval_queue"]:
            if p["id"] == proposal_id:
                p["status"] = "REJECTED"
                p["approved_by"] = user
                p["approved_timestamp"] = time.time()
                self.mem.save()
                log_event("REJECTION", "Proposal rejected", {"id": proposal_id})
                return p
        return None
