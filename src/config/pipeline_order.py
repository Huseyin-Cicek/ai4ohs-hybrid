from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

"""Auto-refactored by ACE/FERS.
This module was touched by the evolutionary refactor pipeline.
"""



PROJECT_ROOT = Path(__file__).resolve().parents[2]

_RELATIVE_STAGE_PATHS: Sequence[Path] = (
    Path("src/pipelines/00_ingest/run.py"),
    Path("src/pipelines/01_staging/run.py"),
    Path("src/pipelines/02_processing/run.py"),
    Path("src/pipelines/03_rag/run.py"),
)


@dataclass(frozen=True)
class PipelineStage:
    """Immutable description of a pipeline stage."""

    name: str
    script: Path

    @property
    def stamp_path(self) -> Path:
        """Destination of the stage completion stamp."""

        return PROJECT_ROOT / "logs" / "pipelines" / f"{self.name}.stamp"

    def as_command(self, python_executable: str) -> List[str]:
        """Return the command used to execute this stage."""

        return [python_executable, str(self.script)]


PIPELINE_STAGES: Sequence[PipelineStage] = tuple(
    PipelineStage(name=relative.parent.name, script=PROJECT_ROOT / relative)
    for relative in _RELATIVE_STAGE_PATHS
)


def iter_pipeline_stages() -> Iterable[PipelineStage]:
    """Yield configured pipeline stages in execution order."""

    return iter(PIPELINE_STAGES)
