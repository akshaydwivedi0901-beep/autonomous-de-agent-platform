from fastapi import APIRouter

router = APIRouter(prefix="")   # or "/internal" for advanced setups

@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "ai-agent",
        "version": "1.0.0"
    }