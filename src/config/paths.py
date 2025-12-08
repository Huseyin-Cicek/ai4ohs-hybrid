from .settings import settings
from pathlib import Path

"""Auto-refactored by ACE/FERS.
This module was touched by the evolutionary refactor pipeline.
"""



RAW_ROOT = Path(settings.RAW_ROOT).expanduser()
CLEAN_ROOT = Path(settings.CLEAN_ROOT).expanduser()
LOG_ROOT = Path(settings.LOG_ROOT).expanduser()
RAW_ROOT.mkdir(parents=True, exist_ok=True)
CLEAN_ROOT.mkdir(parents=True, exist_ok=True)
LOG_ROOT.mkdir(parents=True, exist_ok=True)

# Raw subpaths
RAW_SOURCES = RAW_ROOT / "00_sources"
RAW_STAGING = RAW_ROOT / "01_staging"
RAW_PROC    = RAW_ROOT / "02_processing"
for p in [RAW_SOURCES, RAW_STAGING, RAW_PROC]:
    p.mkdir(parents=True, exist_ok=True)

# Clean curated
CLEAN_ENTITIES = CLEAN_ROOT / "entities"
CLEAN_MARTS = CLEAN_ROOT / "marts"
CLEAN_EXPORTS = CLEAN_ROOT / "exports"
for p in [CLEAN_ENTITIES, CLEAN_MARTS, CLEAN_EXPORTS]:
    p.mkdir(parents=True, exist_ok=True)

# Artifacts
INDEX_DIR = RAW_PROC / "faiss"
INDEX_DIR.mkdir(parents=True, exist_ok=True)
CHUNK_DIR = RAW_PROC / "chunks"
CHUNK_DIR.mkdir(parents=True, exist_ok=True)
EMB_DIR = RAW_PROC / "embeddings"
EMB_DIR.mkdir(parents=True, exist_ok=True)
HYBRID_DIR = RAW_PROC / "hybrid_indexes"
HYBRID_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACTS_MANIFEST = CLEAN_ROOT / "artifacts_manifest.json"
