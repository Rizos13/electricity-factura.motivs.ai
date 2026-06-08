from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel


router = APIRouter(prefix="/api", tags=["config"])


class ClientConfig(BaseModel):
    bug_report_enabled: bool
    hosted_mode: bool
    local_install_url: str


@router.get("/config", response_model=ClientConfig)
async def client_config(request: Request) -> ClientConfig:
    settings = request.app.state.settings
    token = getattr(settings, "github_token", "") or ""
    repo = getattr(settings, "bug_report_repo", "") or ""
    return ClientConfig(
        bug_report_enabled=bool(token and repo),
        hosted_mode=getattr(settings, "hosted_mode", False),
        local_install_url=getattr(settings, "local_install_url", ""),
    )
