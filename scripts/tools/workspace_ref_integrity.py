import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # ai4ohs-hybrid
INTERACTION_MAP = ROOT / "logs" / "workspace-interaction-map.json"
REPORT_OUT = ROOT / "logs" / "workspace-ref-report.json"

# AI4OHS çekirdek alanlar (korunacak domainler)
CORE_PREFIXES = (
    "src/agentic/",
    "src/ai_ml/",
    "src/genai/",
    "src/governance/",
    "src/ohs/",
    "src/pipelines/",
    "src/reporting/",
    "src/utils/",
    "scripts/prod/",
    "scripts/dev/",
    "config/",
)

# Açıkça farklı domain: ai4crypto
SEPARATE_DOMAIN_PREFIXES = (
    "H:/DataLake/ai4crypto-raw/",
    "H:/DataWarehouse/ai4crypto-clean/",
)


def load_interaction_map():
    if not INTERACTION_MAP.exists():
        raise FileNotFoundError(f"Map not found: {INTERACTION_MAP}")
    with INTERACTION_MAP.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_interaction_map(raw: dict):
    """
    Desteklenen formatlar:
    1) {"nodes": {...}, "edges": [{"from": "...", "to": "..."}]}
    2) Adjacency dict: {"file_a.py": ["dep1.py", "dep2.py"], ...}
    """
    if not raw:
        raise ValueError("Interaction map is empty.")

    if "nodes" in raw and "edges" in raw:
        return raw

    if isinstance(raw, dict):
        edges = []
        nodes = {}
        for src, targets in raw.items():
            nodes[src] = {}
            if targets:
                for tgt in targets:
                    edges.append({"from": src, "to": tgt})
                    nodes.setdefault(tgt, {})
        return {"nodes": nodes, "edges": edges}

    raise ValueError("Unsupported interaction map format.")


def classify_files(structure_map: dict):
    nodes = structure_map.get("nodes", {})
    edges = structure_map.get("edges", [])

    if not nodes and not edges:
        raise ValueError("Interaction map contains no nodes/edges after normalization.")

    in_deg = {n: 0 for n in nodes}
    out_deg = {n: 0 for n in nodes}

    for e in edges:
        src = e["from"]
        tgt = e["to"]
        if src in out_deg:
            out_deg[src] += 1
        if tgt in in_deg:
            in_deg[tgt] += 1

    core_files = []
    candidate_integrate = []
    candidate_prune = []

    for path in nodes:
        # Sadece .py dosyalara odaklan
        if not path.endswith(".py"):
            continue

        score = in_deg[path] + out_deg[path]

        if path.startswith(SEPARATE_DOMAIN_PREFIXES):
            # farklı domain
            candidate_prune.append({"path": path, "reason": "separate_domain", "score": score})
            continue

        if path.startswith(CORE_PREFIXES):
            if score > 0:
                core_files.append({"path": path, "score": score})
            else:
                candidate_integrate.append({"path": path, "reason": "orphan_core", "score": score})
        else:
            # ne core ne de ayrı domain
            candidate_prune.append({"path": path, "reason": "orphan_misc", "score": score})

    return {
        "core": core_files,
        "candidate_integrate": candidate_integrate,
        "candidate_prune": candidate_prune,
    }


def main():
    os.makedirs(ROOT / "logs", exist_ok=True)
    structure_raw = load_interaction_map()
    structure_map = normalize_interaction_map(structure_raw)
    result = classify_files(structure_map)

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUT, "w", encoding="utf8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"[REF] Report written to: {REPORT_OUT}")


if __name__ == "__main__":
    main()
