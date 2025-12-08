#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
00_ingest pipeline runner.

Bu dosya hem:
    - python -m src.pipelines.00_ingest.run
hem de:
    - python src/pipelines/00_ingest/run.py
şeklinde çağrıldığında çalışacak şekilde tasarlanmıştır.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------
# Dynamic project root resolution so that "import src.XXX" works
# even when run as "python src/pipelines/00_ingest/run.py"
# ---------------------------------------------------------------------
CURRENT_FILE = Path(__file__).resolve()
# .../src/pipelines/00_ingest/run.py
# parents[0] = 00_ingest
# parents[1] = pipelines
# parents[2] = src
# parents[3] = project root
PROJECT_ROOT = CURRENT_FILE.parents[3]
SRC_ROOT = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# Artık "src" paketi import edilebilir
from src.utils.stamps import write_stamp_atomic  # noqa: E402
from src.utils.path_sanitize import sanitize_path  # noqa: E402
from src.utils.io_safe import read_text_safe  # noqa: E402

STAGE_NAME = "00_ingest"


def main() -> None:
    """Entry point for 00_ingest pipeline."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] Running {STAGE_NAME} pipeline...")

    # logs/pipelines klasörünü proje köküne göre tanımla
    stamp_dir = PROJECT_ROOT / "logs" / "pipelines"
    stamp_dir.mkdir(parents=True, exist_ok=True)

    # İnce RAG-ingest uyumu: sanitize + clean helper'larını hazırla (no-op örnek)
    sample_path = sanitize_path("data/raw/sample.txt")
    # Basit okuma; gerçek temizleme mantığı ingest pipeline'ında uygulanmalıdır.
    _ = read_text_safe(sample_path) if Path(sample_path).exists() else ""

    # Buraya 00_ingest'in gerçek iş mantığını ekleyebilirsin.
    # Şu an sadece atomic bir stamp üretiyor.
    write_stamp_atomic(stamp_dir, STAGE_NAME)

    ts_done = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts_done}] {STAGE_NAME} completed.")


if __name__ == "__main__":
    main()
