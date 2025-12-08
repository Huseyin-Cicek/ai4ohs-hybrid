import ast
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------
EXCLUDED_DIRS = {
    ".venv",
    ".cache",
    ".github",
    ".ruff_cache",
    ".pytest_cache",
    ".mypy_cache",
    ".idea",
    ".git",
    "__pycache__",
    "sandbox_repo",
    "logs",
    "data",
    "models",
    "reports",
    "docs",
    "DataLake",
    "DataWarehouse",
}

WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_ROOT", Path.cwd()))
LOGS_DIR = WORKSPACE_ROOT / "logs"
STRUCTURE_FILE = LOGS_DIR / "workspace-structure.txt"
INIT_LOG_FILE = LOGS_DIR / "workspace-init-log.txt"
INTERACTION_TXT = LOGS_DIR / "workspace-interaction-map.txt"
INTERACTION_JSON = LOGS_DIR / "workspace-interaction-map.json"
DEPENDENCY_JSON = LOGS_DIR / "workspace-dependency-report.json"
DEPENDENCY_TXT = LOGS_DIR / "workspace-dependency-report.txt"


# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------
def ensure_logs_dir() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def human_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{num_bytes} B"


def should_skip_dir(path: Path) -> bool:
    return path.name in EXCLUDED_DIRS


# -------------------------------------------------------------------
# 1) DIRECTORY STRUCTURE + SIZES
# -------------------------------------------------------------------
def build_directory_structure(root: Path) -> Tuple[str, int, int, int]:
    """
    Returns:
        structure_str: tree-like structure as text
        total_files: int
        total_dirs: int
        total_bytes: int
    """
    lines: List[str] = []
    total_files = 0
    total_dirs = 0
    total_bytes = 0

    root_str = root.name
    lines.append(f"{root_str}/")

    def walk(current: Path, prefix: str = "") -> None:
        nonlocal total_files, total_dirs, total_bytes

        # children: dirs + files, skip excluded dirs
        entries = sorted(
            [p for p in current.iterdir() if not (p.is_dir() and should_skip_dir(p))],
            key=lambda p: (not p.is_dir(), p.name.lower()),
        )

        count = len(entries)
        for idx, entry in enumerate(entries):
            is_last = idx == count - 1
            connector = "└── " if is_last else "├── "
            next_prefix = prefix + ("    " if is_last else "│   ")

            if entry.is_dir():
                total_dirs += 1
                lines.append(f"{prefix}{connector}{entry.name}/")
                walk(entry, next_prefix)
            else:
                total_files += 1
                try:
                    size = entry.stat().st_size
                except OSError:
                    size = 0
                total_bytes += size
                size_str = human_size(size)
                lines.append(f"{prefix}{connector}{entry.name} ({size_str})")

    walk(root)
    return "\n".join(lines), total_files, total_dirs, total_bytes


# -------------------------------------------------------------------
# 2) PYTHON MODULE MAP + IMPORT-BASED INTERACTION MAP
# -------------------------------------------------------------------
def collect_python_files(root: Path) -> List[Path]:
    py_files: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # filter out excluded dirs in-place for os.walk
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]

        for fname in filenames:
            if fname.endswith(".py"):
                py_files.append(Path(dirpath) / fname)
    return py_files


def build_module_map(py_files: List[Path]) -> Dict[str, Path]:
    """
    Map "package.module" → Path
    e.g. src/agentic/auto_refactor/ace_executor.py → "src.agentic.auto_refactor.ace_executor"
    __init__.py → module name without "__init__"
    """
    module_map: Dict[str, Path] = {}
    for f in py_files:
        rel = f.relative_to(WORKSPACE_ROOT)
        parts = list(rel.parts)
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1].replace(".py", "")
        if not parts:
            continue
        mod_name = ".".join(parts)
        module_map[mod_name] = f
        # Alias: src/ prefix olmadan da kaydet (import ai_ml.... için)
        if parts and parts[0] == "src":
            alias = ".".join(parts[1:])
            if alias and alias not in module_map:
                module_map[alias] = f
    return module_map


def extract_imports(py_file: Path) -> Set[str]:
    """
    Returns set of imported module paths as strings.
    """
    imports: Set[str] = set()
    try:
        src = py_file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return imports
    except OSError:
        return imports

    try:
        tree = ast.parse(src)
    except SyntaxError:
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name:
                    imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                # from X import Y
                imports.add(node.module)
            else:
                # from . import something (relative)
                # just mark as relative to this module
                imports.add("._relative")
    return imports


def resolve_interactions(py_files: List[Path], module_map: Dict[str, Path]) -> Dict[str, List[str]]:
    """
    For each Python file, returns list of other workspace files it imports.
    """
    # reverse map: Path -> module_name
    path_to_mod: Dict[Path, str] = {v: k for k, v in module_map.items()}

    interactions: Dict[str, List[str]] = {}
    for f in py_files:
        rel_f = str(f.relative_to(WORKSPACE_ROOT)).replace("\\", "/")
        imported_files: Set[str] = set()

        imports = extract_imports(f)
        if not imports:
            interactions[rel_f] = []
            continue

        # Own module name (for resolving relative imports if needed later)
        own_mod = path_to_mod.get(f)

        for mod in imports:
            if mod == "._relative":
                # Rough handling of relative imports:
                # we don't try to fully resolve here, just note that file has internal deps
                continue

            # direct exact match
            if mod in module_map:
                target = module_map[mod]
                rel_target = str(target.relative_to(WORKSPACE_ROOT)).replace("\\", "/")
                imported_files.add(rel_target)
                continue

            # try prefix matches (e.g. importing a package, not the exact file)
            matches = [p for m, p in module_map.items() if m == mod or m.startswith(mod + ".")]
            for p in matches:
                rel_target = str(p.relative_to(WORKSPACE_ROOT)).replace("\\", "/")
                imported_files.add(rel_target)

        interactions[rel_f] = sorted(imported_files)

    return interactions


def format_interaction_text(interactions: Dict[str, List[str]]) -> str:
    """
    Generate human-readable text map of file interactions.
    """
    lines: List[str] = []
    for src_file, deps in sorted(interactions.items()):
        lines.append(f"FILE: {src_file}")
        if not deps:
            lines.append("  -> (no local dependencies)")
        else:
            for d in deps:
                lines.append(f"  -> {d}")
        lines.append("")  # empty line between files
    return "\n".join(lines)


def to_nodes_edges(interactions: Dict[str, List[str]]) -> Dict[str, object]:
    """
    Build a nodes/edges map for downstream tools.
    """
    nodes = {src: {} for src in interactions}
    edges = []
    for src, deps in interactions.items():
        for dep in deps:
            nodes.setdefault(dep, {})
            edges.append({"from": src, "to": dep})
    return {"nodes": nodes, "edges": edges, "adjacency": interactions}


def summarize_dependencies(interactions: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Calculates inbound/outbound dependency summaries.
    Returns:
      {
        "no_outbound": [...],  # dosya başka yere import yapmıyor
        "no_inbound": [...],   # hiçbir dosya bu dosyayı import etmiyor
        "double_orphans": [...],  # hem inbound hem outbound yok
      }
    """
    inbound_count: Dict[str, int] = {f: 0 for f in interactions}
    for src, deps in interactions.items():
        for dep in deps:
            inbound_count[dep] = inbound_count.get(dep, 0) + 1

    no_outbound = [f for f, deps in interactions.items() if not deps]
    no_inbound = [f for f, cnt in inbound_count.items() if cnt == 0]
    double_orphans = sorted(set(no_outbound) & set(no_inbound))

    return {
        "no_outbound": sorted(no_outbound),
        "no_inbound": sorted(no_inbound),
        "double_orphans": double_orphans,
    }


def format_dependency_text(summary: Dict[str, List[str]]) -> str:
    lines: List[str] = []
    lines.append("Dependency Summary")
    lines.append("-------------------")
    lines.append(f"No outbound deps: {len(summary['no_outbound'])}")
    for f in summary["no_outbound"]:
        lines.append(f"  - {f}")
    lines.append("")
    lines.append(f"No inbound refs: {len(summary['no_inbound'])}")
    for f in summary["no_inbound"]:
        lines.append(f"  - {f}")
    lines.append("")
    lines.append(f"Double orphans (no in/out): {len(summary['double_orphans'])}")
    for f in summary["double_orphans"]:
        lines.append(f"  - {f}")
    lines.append("")
    lines.append("Not: Bunlar entegrasyon adayıdır; görev/pipeline/agent içinde kullanıma bağlayın.")
    return "\n".join(lines)


# -------------------------------------------------------------------
# 3) INIT LOG
# -------------------------------------------------------------------
def write_init_log(
    total_files: int,
    total_dirs: int,
    total_bytes: int,
    profile_hint: str = "",
) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"Workspace Init Log - {now}",
        f"Root: {WORKSPACE_ROOT}",
        "",
        f"Total directories: {total_dirs}",
        f"Total files     : {total_files}",
        f"Total size      : {human_size(total_bytes)}",
        "",
        f"Excluded dirs   : {', '.join(sorted(EXCLUDED_DIRS))}",
    ]
    if profile_hint:
        lines.append(f"Profile hint    : {profile_hint}")
    lines.append("")

    INIT_LOG_FILE.write_text("\n".join(lines), encoding="utf-8")


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
def main():
    ensure_logs_dir()

    # 1) Directory structure + sizes
    structure_str, total_files, total_dirs, total_bytes = build_directory_structure(WORKSPACE_ROOT)
    STRUCTURE_FILE.write_text(structure_str, encoding="utf-8")

    # 2) Python files + interaction map
    py_files = collect_python_files(WORKSPACE_ROOT)
    module_map = build_module_map(py_files)
    interactions = resolve_interactions(py_files, module_map)

    # 2a) Text interaction map
    interaction_text = format_interaction_text(interactions)
    INTERACTION_TXT.write_text(interaction_text, encoding="utf-8")

    # 2b) JSON interaction map
    interaction_struct = to_nodes_edges(interactions)
    INTERACTION_JSON.write_text(
        json.dumps(interaction_struct, indent=2),
        encoding="utf-8",
    )

    # 2c) Dependency summary (inbound/outbound)
    dep_summary = summarize_dependencies(interactions)
    DEPENDENCY_JSON.write_text(json.dumps(dep_summary, indent=2), encoding="utf-8")
    DEPENDENCY_TXT.write_text(format_dependency_text(dep_summary), encoding="utf-8")

    # 3) Init log
    write_init_log(
        total_files=total_files,
        total_dirs=total_dirs,
        total_bytes=total_bytes,
        profile_hint="",  # istersen ACE/FERS profilini buraya inject edebilirsin
    )

    print(f"[OK] Workspace structure written to: {STRUCTURE_FILE}")
    print(f"[OK] Workspace init log written to: {INIT_LOG_FILE}")
    print(f"[OK] Interaction map (text) written to: {INTERACTION_TXT}")
    print(f"[OK] Interaction map (json) written to: {INTERACTION_JSON}")
    print(f"[OK] Dependency summary written to: {DEPENDENCY_TXT}")


if __name__ == "__main__":
    main()
