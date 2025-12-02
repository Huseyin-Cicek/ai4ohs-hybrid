#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
03_rag pipeline runner.

Bu dosya hem:
    - python -m src.pipelines.03_rag.run
hem de:
    - python src/pipelines/03_rag/run.py
şeklinde çağrıldığında çalışacak şekilde tasarlanmıştır.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
# .../src/pipelines/03_rag/run.py
# parents[0] = 03_rag
# parents[1] = pipelines
# parents[2] = src
# parents[3] = project root
PROJECT_ROOT = CURRENT_FILE.parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.stamps import write_stamp_atomic  # noqa: E402

STAGE_NAME = "03_rag"


def main() -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] Running {STAGE_NAME} pipeline...")

    stamp_dir = PROJECT_ROOT / "logs" / "pipelines"
    stamp_dir.mkdir(parents=True, exist_ok=True)

    # Buraya 03_rag aşamasının gerçek RAG index build / refresh mantığını ekleyebilirsin.
    write_stamp_atomic(stamp_dir, STAGE_NAME)

    ts_done = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts_done}] {STAGE_NAME} completed.")


if __name__ == "__main__":
    main()
