from .routers import datasets, guardrails, health, search
from fastapi import FastAPI

"""Auto-refactored by ACE/FERS.
This module was touched by the evolutionary refactor pipeline.
"""


"""Auto-refactored by ACE/FERS.
This module was touched by the evolutionary refactor pipeline.
"""


"""Auto-refactored by ACE/FERS.
This module was touched by the evolutionary refactor pipeline.
"""



app = FastAPI(title="AI4OHS-HYBRID API")

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(search.router, prefix="/search", tags=["rag"])
app.include_router(guardrails.router, prefix="/validate", tags=["cag"])
app.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
