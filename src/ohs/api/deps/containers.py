from pathlib import Path
from pydantic import BaseSettings

"""Auto-refactored by ACE/FERS.
This module was touched by the evolutionary refactor pipeline.
"""


"""Auto-refactored by ACE/FERS.
This module was touched by the evolutionary refactor pipeline.
"""


"""Auto-refactored by ACE/FERS.
This module was touched by the evolutionary refactor pipeline.
"""




class Settings(BaseSettings):
    RAW_ROOT: str = r"H:/DataLake/ai4hsse-raw"
    CLEAN_ROOT: str = r"H:/DataWarehouse/ai4hsse-clean"
    LOG_ROOT: str = str(Path("logs"))
    OFFLINE_MODE: bool = True
    GPU_ACCELERATION: bool = True
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L12-v2"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"


settings = Settings()
