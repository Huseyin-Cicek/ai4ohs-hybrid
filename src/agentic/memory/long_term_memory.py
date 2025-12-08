"""
Long-Term Memory (Learning Enabled)
Öğrenme modeli system_prompts.yaml + learning_memory_schema.json ile uyumludur.
:contentReference[oaicite:3]{index=3}
"""

import json
import time

MEMORY_FILE = "data/memory/learning_memory.json"


class LongTermMemory:
    def __init__(self):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                self.memory = json.load(f)
        except:
            self.memory = {
                "version": "2.0",
                "last_updated": time.time(),
                "user_preferences": {},
                "project_context": {},
                "templates": {},
                "regulation_notes": [],
                "corrections_log": [],
            }

    def save(self):
        self.memory["last_updated"] = time.time()
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, indent=2)

    def update_user_preference(self, key, value):
        self.memory.setdefault("user_preferences", {})[key] = value
        self.save()

    def log_correction(self, previous, correction):
        self.memory.setdefault("corrections_log", []).append(
            {"timestamp": time.time(), "previous_output": previous, "user_correction": correction}
        )
        self.save()

    def update_project_context(self, key, value):
        arr = self.memory.setdefault("project_context", {}).setdefault(key, [])
        if value not in arr:
            arr.append(value)
        self.save()

    def update_template(self, t_type, t_data):
        arr = self.memory.setdefault("templates", {}).setdefault(t_type, [])
        arr.append(t_data)
        self.save()
