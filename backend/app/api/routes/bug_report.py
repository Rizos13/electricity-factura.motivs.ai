from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api", tags=["bug-report"])
logger = logging.getLogger(__name__)

_GITHUB_REPO = "Rizos13/electricity-factura.motivs.ai"
_LABELS = ["bug", "user-report"]


class BugReportBody(BaseModel):
    description: str = Field(min_length=10, max_length=5000)
    email: str | None = Field(default=None, max_length=160)
    factura_text: str | None = Field(default=None, max_length=8000)


@router.post("/bug-report")
async def bug_report(body: BugReportBody, request: Request) -> dict[str, object]:
    token = getattr(request.app.state.settings, "github_token", "") or ""
    if not token:
        raise HTTPException(status_code=503, detail="Bug reporting is not configured")

    parts: list[str] = ["## Description", "", body.description.strip(), ""]
    if body.email:
        parts.extend(["**Contact:**", body.email.strip(), ""])
    if body.factura_text:
        parts.extend(["## Pasted factura data", "", "```", body.factura_text.strip()[:6000], "```", ""])
    parts.append("---")
    parts.append("Reported via electricity-factura.motivs.ai bug form")
    issue_body = "\n".join(parts)
    title = f"user report: {body.description.strip().splitlines()[0][:70]}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.post(
            f"https://api.github.com/repos/{_GITHUB_REPO}/issues",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={"title": title, "body": issue_body, "labels": _LABELS},
        )
    if res.status_code >= 300:
        logger.error("github_issue_failed", extra={"status": res.status_code, "body": res.text[:200]})
        raise HTTPException(status_code=502, detail=f"GitHub API error {res.status_code}")
    data = res.json()
    return {"ok": True, "issue_url": data.get("html_url"), "issue_number": data.get("number")}
