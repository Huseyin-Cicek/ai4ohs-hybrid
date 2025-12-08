"""
Basit CAG kural motoru yükleyicisi.
- Kurallar: JSON (örn. src/cag/rules/rules_example.json)
- Standart haritası: JSON (örn. src/cag/standards_map.json)

Özellikler:
- Kuralları belleğe alır, standart/kategori filtresi yapar.
- Strictness önceliğini standards_map içindeki priority_order'a göre uygular.
- Offline-first; ağ erişimi veya dış bağımlılık yok.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class CAGRule:
    rule_id: str
    standard: str
    clause: str
    category: str
    severity: str
    requirement: str
    remediation: str
    match: Dict


class CAGRulesEngine:
    def __init__(
        self,
        rules_path: Path | str = Path("src/cag/rules/rules_example.json"),
        standards_map_path: Path | str = Path("src/cag/standards_map.json"),
    ) -> None:
        self.rules_path = Path(rules_path)
        self.standards_map_path = Path(standards_map_path)
        self.rules: List[CAGRule] = []
        self.standards_map: Dict = {}
        self.strictness_priority: List[str] = []
        self._load_all()

    def _load_all(self) -> None:
        self.rules = self._load_rules(self.rules_path)
        self.standards_map = self._load_json(self.standards_map_path)
        self.strictness_priority = self.standards_map.get("priority_order", [])

    def _load_json(self, path: Path) -> Dict:
        if not path.exists():
            raise FileNotFoundError(f"Standards/Rules dosyası bulunamadı: {path}")
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _load_rules(self, path: Path) -> List[CAGRule]:
        data = self._load_json(path)
        rules_raw = data.get("rules", [])
        loaded: List[CAGRule] = []
        for r in rules_raw:
            loaded.append(
                CAGRule(
                    rule_id=r["rule_id"],
                    standard=r["standard"],
                    clause=r.get("clause", ""),
                    category=r["category"],
                    severity=r["severity"],
                    requirement=r["requirement"],
                    remediation=r.get("remediation", ""),
                    match=r.get("match", {}),
                )
            )
        return loaded

    def reload(self) -> None:
        """Dosyalardan yeniden yükle."""
        self._load_all()

    def list_rules(
        self,
        standard: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[CAGRule]:
        items = self.rules
        if standard:
            items = [r for r in items if r.standard.lower() == standard.lower()]
        if category:
            items = [r for r in items if r.category.lower() == category.lower()]
        return items

    def get_cross_refs(self) -> List[Dict]:
        return self._load_json(self.rules_path).get("cross_refs", [])

def get_strictest_for_topic(self, topic: str) -> Optional[str]:
        """Standards_map içindeki topic için strictest'i döndür."""
        for item in self.standards_map.get("mappings", []):
            if item.get("topic") == topic:
                return item.get("strictest")
        return None


def load_default_cag_engine() -> CAGRulesEngine:
    """Convenience loader for default rulepack."""

    return CAGRulesEngine()


__all__ = ["CAGRulesEngine", "CAGRule", "load_default_cag_engine"]
