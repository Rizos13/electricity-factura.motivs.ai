from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str


class ReadinessResponse(BaseModel):
    status: str
    contracts_loaded: bool
    message: str | None = None


@router.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    return HealthResponse(status="ok", service="electricity-factura-api")


@router.get("/readyz", response_model=ReadinessResponse)
async def readyz() -> ReadinessResponse:
    return ReadinessResponse(status="ready", contracts_loaded=False)
