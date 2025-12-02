from fastapi import FastAPI

from .routers import datasets, guardrails, health, search

app = FastAPI(title="AI4OHS-HYBRID API")

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(search.router, prefix="/search", tags=["rag"])
app.include_router(guardrails.router, prefix="/validate", tags=["cag"])
app.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
