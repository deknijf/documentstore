from fastapi import APIRouter

from app import legacy_main

router = APIRouter()


@router.get("/api/health")
def health() -> dict:
    return legacy_main.health()

