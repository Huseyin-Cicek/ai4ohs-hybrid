from fastapi import APIRouter, Query

router = APIRouter()
@router.get("")
def search(q: str = Query(..., min_length=1)):
    # Placeholder RAG search
    return {"query": q, "results": []}
