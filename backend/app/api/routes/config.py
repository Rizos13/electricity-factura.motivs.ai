from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel


router = APIRouter(prefix="/api", tags=["config"])


class ClientConfig(BaseModel):
    bug_report_enabled: bool


@router.get("/config", response_model=ClientConfig)
async def client_config(request: Request) -> ClientConfig:
    token = getattr(request.app.state.settings, "github_token", "") or ""
    return ClientConfig(bug_report_enabled=bool(token))
