from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Check API liveness")
def health() -> dict[str, str]:
    return {"status": "ok"}