from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, Request


async def require_admin(
    request: Request,
    x_admin_token: str | None = Header(default=None),
) -> None:
    expected = getattr(request.app.state.settings, "admin_token", "") or ""
    if not expected:
        raise HTTPException(status_code=503, detail="Admin token is not configured")
    if not x_admin_token or not secrets.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")
