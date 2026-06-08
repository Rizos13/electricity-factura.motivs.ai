from __future__ import annotations

import base64
import hashlib
import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile


router = APIRouter(prefix="/api", tags=["bug-report"])
logger = logging.getLogger(__name__)

_LABELS = ["bug", "user-report"]
_SCREENSHOT_MAX_BYTES = 5 * 1024 * 1024
_SCREENSHOT_ALLOWED = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}


async def _upload_screenshot(client: httpx.AsyncClient, token: str, repo: str, file: UploadFile) -> str | None:
    ext = _SCREENSHOT_ALLOWED.get(file.content_type or "")
    if not ext:
        raise HTTPException(status_code=415, detail="Unsupported screenshot type")
    blob = await file.read()
    if not blob:
        return None
    if len(blob) > _SCREENSHOT_MAX_BYTES:
        raise HTTPException(status_code=413, detail="Screenshot too large")
    digest = hashlib.sha256(blob).hexdigest()[:10]
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = f"bug-screenshots/{ts}-{digest}.{ext}"
    res = await client.put(
        f"https://api.github.com/repos/{repo}/contents/{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={
            "message": f"chore: bug screenshot {ts}",
            "content": base64.b64encode(blob).decode("ascii"),
        },
    )
    if res.status_code >= 300:
        logger.error("github_upload_failed", extra={"status": res.status_code, "body": res.text[:200]})
        raise HTTPException(status_code=502, detail=f"GitHub upload error {res.status_code}")
    data = res.json()
    return (data.get("content") or {}).get("html_url")


@router.post("/bug-report")
async def bug_report(
    request: Request,
    description: str = Form(..., min_length=10, max_length=5000),
    email: str | None = Form(default=None, max_length=160),
    screenshot: UploadFile | None = File(default=None),
) -> dict[str, object]:
    settings = request.app.state.settings
    token = getattr(settings, "github_token", "") or ""
    repo = getattr(settings, "bug_report_repo", "") or ""
    if not token or not repo:
        raise HTTPException(status_code=503, detail="Bug reporting is not configured")

    async with httpx.AsyncClient(timeout=15.0) as client:
        screenshot_url: str | None = None
        if screenshot is not None and screenshot.filename:
            screenshot_url = await _upload_screenshot(client, token, repo, screenshot)

        parts: list[str] = ["## Description", "", description.strip(), ""]
        if email:
            parts.extend(["**Contact:**", email.strip(), ""])
        if screenshot_url:
            parts.extend(["## Screenshot", "", screenshot_url, ""])
        parts.append("---")
        parts.append("Reported via electricity-factura.motivs.ai bug form")
        issue_body = "\n".join(parts)
        title = f"user report: {description.strip().splitlines()[0][:70]}"

        res = await client.post(
            f"https://api.github.com/repos/{repo}/issues",
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
