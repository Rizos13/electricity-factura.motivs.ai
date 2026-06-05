from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Request

from backend.admin.auth import require_admin


router = APIRouter(prefix="/api/motivs", tags=["motivs-admin"])


@router.get("/stats", dependencies=[Depends(require_admin)])
async def stats(request: Request) -> dict[str, Any]:
    settings = request.app.state.settings
    out: dict[str, Any] = {
        "tenant_slug": settings.tenant_slug,
        "factura_contract": str(settings.factura_contract_path),
        "ofertas_contract": str(settings.ofertas_contract_path),
        "total_runs": 0,
        "verdicts": {},
        "module_decisions": {},
        "kind_counts": {},
        "last_run_id": None,
        "last_kind": None,
        "contract_version": None,
    }
    summary_path = settings.motivs_summary_path
    if summary_path.exists():
        try:
            data = json.loads(summary_path.read_text())
            if isinstance(data, dict):
                out.update(data)
        except json.JSONDecodeError:
            pass
    return out
