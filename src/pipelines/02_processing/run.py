from __future__ import annotations
from datetime import datetime
from pathlib import Path
from src.utils.stamps import write_stamp_atomic  # noqa: E402
import sys

"""Auto-refactored by ACE/FERS.
This module was touched by the evolutionary refactor pipeline.
"""

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
02_processing pipeline runner.

Bu dosya hem:
    - python -m src.pipelines.02_processing.run
hem de:
    - python src/pipelines/02_processing/run.py
şeklinde çağrıldığında çalışacak şekilde tasarlanmıştır.
"""



CURRENT_FILE = Path(__file__).resolve()
# .../src/pipelines/02_processing/run.py
# parents[0] = 02_processing
# parents[1] = pipelines
# parents[2] = src
# parents[3] = project root
PROJECT_ROOT = CURRENT_FILE.parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


STAGE_NAME = "02_processing"


def main() -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] Running {STAGE_NAME} pipeline...")

    stamp_dir = PROJECT_ROOT / "logs" / "pipelines"
    stamp_dir.mkdir(parents=True, exist_ok=True)

    # Buraya 02_processing aşamasının gerçek iş mantığını ekleyebilirsin.
    write_stamp_atomic(stamp_dir, STAGE_NAME)

    ts_done = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts_done}] {STAGE_NAME} completed.")


if __name__ == "__main__":
    main()
