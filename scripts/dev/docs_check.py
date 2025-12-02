"""Documentation drift detector for AI4OHS-HYBRID.

This script scans documentation files (Markdown by default) for inline
references to repository files or directories and reports cases where the
referenced paths no longer exist. The goal is to surface gaps between the
written documentation and the actual codebase (e.g., missing modules that the
docs promise, renamed scripts, outdated quick-start commands).

The detector intentionally stays lightweight and offline-friendly: it only uses
Python's standard library and relies on simple heuristics to extract candidate
paths (inline code spans, fenced code blocks, and bullet lists containing
forward slashes). It currently focuses on static assets in the repository and
ignores runtime artefacts such as the `logs/` hierarchy unless explicitly
requested via CLI flags.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Set, Tuple

# Extensions that are meaningful to track inside the repo.
TRACKED_EXTENSIONS: Set[str] = {
    ".py",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".cfg",
    ".ini",
    ".ps1",
    ".psm1",
    ".sh",
    ".bat",
    ".txt",
    ".lock",
    ".csv",
}

# Common prefixes we care about even if they do not contain a file extension.
INTERESTING_PREFIXES: Tuple[str, ...] = (
    "src/",
    "scripts/",
    "tests/",
    "docs/",
    ".vscode/",
    "examples/",
    "requirements",
    "pyproject.toml",
    "setup.cfg",
    "README",
)

# Paths that are typically generated at runtime and should not be treated as
# documentation drift unless explicitly opted in.
DEFAULT_IGNORED_PREFIXES: Tuple[str, ...] = (
    "logs/",
    "logs\\",
    "artifacts/",
)

INLINE_CODE_PATTERN = re.compile(r"`([^`]+)`")
FENCED_BLOCK_PATTERN = re.compile(r"```[\w+-]*\n(.*?)```", re.DOTALL)
PATH_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_./\\-]+")


@dataclass
class DriftIssue:
    """Represents a single documentation drift finding."""

    referenced_path: str
    status: str  # e.g. "missing", "not_checked"


@dataclass
class DriftReport:
    """Aggregated drift report for a single documentation artifact."""

    document: Path
    issues: List[DriftIssue]


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect documentation drift.")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Specific documentation files or directories to scan. Defaults to docs/*.md and README.md",
    )
    parser.add_argument(
        "--include-runtime",
        action="store_true",
        help="Also check runtime/generated folders such as logs/ for drift.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root (auto-detected).",
    )
    return parser.parse_args(argv)


def collect_default_targets(root: Path) -> List[Path]:
    """Return default documentation files to scan."""
    targets: List[Path] = []
    docs_dir = root / "docs"
    if docs_dir.is_dir():
        targets.extend(sorted(docs_dir.rglob("*.md")))
    readme = root / "README.md"
    if readme.exists():
        targets.append(readme)
    return targets


def normalize_candidate(raw: str) -> str:
    """Sanitize a candidate path extracted from the documentation."""
    candidate = raw.strip().strip("'\".,;:()[]{}")
    candidate = candidate.replace("\\", "/")

    # Drop leading ./ or ../ for repo-relative resolution.
    if candidate.startswith("./"):
        candidate = candidate[2:]
    while candidate.startswith("../"):
        candidate = candidate[3:]

    return candidate


def is_interesting_path(candidate: str) -> bool:
    """Determine whether the candidate path should be evaluated."""
    if not candidate or candidate in {"/", ".", ".."}:
        return False
    if "://" in candidate:  # Ignore URLs
        return False

    lower_candidate = candidate.lower()

    # Allowlist prefixes without needing an extension.
    if any(lower_candidate.startswith(prefix) for prefix in INTERESTING_PREFIXES):
        return True

    # Include if the path ends with a known extension.
    for ext in TRACKED_EXTENSIONS:
        if lower_candidate.endswith(ext.lower()):
            return True

    # Directories that end with a slash.
    if candidate.endswith("/") and candidate.count("/") >= 1:
        return True

    return False


def extract_candidates(text: str) -> Set[str]:
    """Extract candidate repo paths from a documentation string."""
    candidates: Set[str] = set()

    # Inline code spans
    for inline in INLINE_CODE_PATTERN.findall(text):
        if "/" in inline or any(inline.endswith(ext) for ext in TRACKED_EXTENSIONS):
            candidates.add(normalize_candidate(inline))

    # Fenced code blocks
    for block in FENCED_BLOCK_PATTERN.findall(text):
        for token in PATH_TOKEN_PATTERN.findall(block):
            if "/" in token or any(token.endswith(ext) for ext in TRACKED_EXTENSIONS):
                candidates.add(normalize_candidate(token))

    # General scan for bullet lines referencing paths (e.g. "- src/core/file.py")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("-", "*", "•")) and "/" in stripped:
            for token in PATH_TOKEN_PATTERN.findall(stripped):
                if "/" in token:
                    candidates.add(normalize_candidate(token))

    return {path for path in candidates if is_interesting_path(path)}


def should_ignore(path: str, include_runtime: bool) -> bool:
    if include_runtime:
        return False
    return path.startswith(DEFAULT_IGNORED_PREFIXES)


def evaluate_document(
    document: Path,
    repo_root: Path,
    include_runtime: bool,
) -> DriftReport:
    text = document.read_text(encoding="utf-8")
    candidates = extract_candidates(text)

    issues: List[DriftIssue] = []
    for candidate in sorted(candidates):
        if should_ignore(candidate, include_runtime):
            continue

        normalized = candidate.rstrip("/")
        target_path = (repo_root / normalized).resolve()

        # Ensure the resolved path stays within the repo root to avoid surprises.
        try:
            target_path.relative_to(repo_root)
        except ValueError:
            issues.append(DriftIssue(candidate, "out_of_repo_scope"))
            continue

        if not target_path.exists():
            issues.append(DriftIssue(candidate, "missing"))

    return DriftReport(document=document, issues=issues)


def print_report(reports: Iterable[DriftReport]) -> int:
    """Pretty-print report to stdout and return recommended exit code."""
    missing_total = 0
    out_of_scope_total = 0

    print("Docs Drift Detector")
    print("====================")
    has_findings = False

    for report in reports:
        if not report.issues:
            continue

        has_findings = True
        print(f"\nDocument: {report.document.relative_to(report.document.parents[2])}")
        for issue in report.issues:
            if issue.status == "missing":
                missing_total += 1
                print(f"  - missing: {issue.referenced_path}")
            elif issue.status == "out_of_repo_scope":
                out_of_scope_total += 1
                print(f"  - out-of-scope: {issue.referenced_path}")

    if not has_findings:
        print("\nNo documentation drift detected.")
        return 0

    print("\nSummary:")
    if missing_total:
        print(f"  • Missing paths: {missing_total}")
    if out_of_scope_total:
        print(f"  • Out-of-repo references: {out_of_scope_total}")

    print(
        "\nDrift detected. Please update the documentation or (re)introduce the referenced assets."
    )
    return 1


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    repo_root: Path = args.root.resolve()

    if not repo_root.exists():
        print(f"Repository root does not exist: {repo_root}", file=sys.stderr)
        return 2

    if args.paths:
        targets: List[Path] = []
        for raw_path in args.paths:
            candidate = Path(raw_path)
            if candidate.is_dir():
                targets.extend(sorted(candidate.rglob("*.md")))
            else:
                targets.append(candidate)
    else:
        targets = collect_default_targets(repo_root)

    if not targets:
        print("No documentation files found to scan.")
        return 0

    reports: List[DriftReport] = []
    for target in targets:
        doc_path = target if target.is_absolute() else (repo_root / target)
        if not doc_path.exists():
            print(f"Warning: documentation target not found: {doc_path}")
            continue
        reports.append(evaluate_document(doc_path, repo_root, args.include_runtime))

    return print_report(reports)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
