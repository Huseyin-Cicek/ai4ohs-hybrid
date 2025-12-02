from fastapi import APIRouter

router = APIRouter()
@router.get("")
def list_datasets():
    # Placeholder dataset listing
    return {"datasets": ["incidents","ncr","sof","trainings"]}
