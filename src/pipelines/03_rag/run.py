from __future__ import annotations
from datetime import datetime
from pathlib import Path
import sys

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]
SRC_ROOT = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from src.utils.stamps import write_stamp_atomic  # noqa: E402

# RAG helpers (lightweight warm imports to ensure integration)
from genai.rag.chunker import apply_rules  # noqa: E402
from genai.rag.document_loader import load_document  # noqa: E402
from genai.rag.reranker_v3 import rerank_v3  # noqa: E402
from genai.rag.ocr_ingest import ingest_image_to_chunks  # noqa: E402

"""Auto-refactored by ACE/FERS.
This module was touched by the evolutionary refactor pipeline.
"""

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



CURRENT_FILE = Path(__file__).resolve()
# .../src/pipelines/03_rag/run.py
# parents[0] = 03_rag
# parents[1] = pipelines
# parents[2] = src
# parents[3] = project root
PROJECT_ROOT = CURRENT_FILE.parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


STAGE_NAME = "03_rag"


def main() -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] Running {STAGE_NAME} pipeline...")

    stamp_dir = PROJECT_ROOT / "logs" / "pipelines"
    stamp_dir.mkdir(parents=True, exist_ok=True)

    # RAG warmup: temel modülleri çalıştırarak entegrasyonu doğrula
    sample = "OHS sample regulation text."
    _ = apply_rules(sample, doc_type="general")
    _ = rerank_v3("sample query", [{"text": sample, "meta": {}}], llama_scorer=None, top_k=1)
    _ = ingest_image_to_chunks  # reference for OCR pipeline (no execution)
    _ = load_document  # reference for loader (no execution)

    write_stamp_atomic(stamp_dir, STAGE_NAME)

    ts_done = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts_done}] {STAGE_NAME} completed.")


if __name__ == "__main__":
    main()
