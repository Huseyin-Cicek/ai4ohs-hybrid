import json
import os
import time

"""
Audit Logger – AI4OHS-HYBRID (Enhanced)
Amaç:
- Her üretimi izlenebilir kılmak,
- Kullanılan RAG kaynaklarını,
- Uygulanan mevzuat maddelerini,
- AgenticAI döngü adımlarını loglamak.
"""


LOG_FILE = "logs/audit_log.jsonl"


def log_event(event_type, message, metadata=None):
    entry = {
        "timestamp": time.time(),
        "event": event_type,
        "message": message,
        "metadata": metadata or {},
    }
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def log_generation(prompt, output, compliance_map, rag_sources):
    entry = {
        "timestamp": time.time(),
        "prompt": prompt,
        "output": output,
        "compliance_mapping": compliance_map,
        "rag_sources": rag_sources,
    }
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
