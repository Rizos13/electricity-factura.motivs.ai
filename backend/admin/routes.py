from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from backend.admin.auth import require_admin


router = APIRouter(prefix="/api/motivs", tags=["motivs-admin"])


def _read_runs(path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    runs: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            try:
                runs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return runs


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


@router.get("/runs", dependencies=[Depends(require_admin)])
async def runs_list(
    request: Request,
    limit: int = Query(default=50, ge=1, le=500),
    kind: str | None = Query(default=None, pattern="^(factura|ofertas)$"),
) -> dict[str, Any]:
    settings = request.app.state.settings
    runs = _read_runs(settings.motivs_runs_path)
    if kind:
        runs = [r for r in runs if r.get("kind") == kind]
    total = len(runs)
    sliced = runs[-limit:]
    sliced.reverse()
    return {"total": total, "returned": len(sliced), "runs": sliced}


@router.get("/runs/{run_id}/detail", dependencies=[Depends(require_admin)])
async def run_detail(run_id: str, request: Request) -> dict[str, Any]:
    settings = request.app.state.settings
    for run in _read_runs(settings.motivs_runs_path):
        if run.get("run_id") == run_id:
            return run
    raise HTTPException(status_code=404, detail="Run not found")


@router.get("/snapshot-status", dependencies=[Depends(require_admin)])
async def snapshot_status(request: Request) -> dict[str, Any]:
    settings = request.app.state.settings
    offers_path = settings.artifact_dir / "offers.jsonl"
    if not offers_path.exists():
        return {
            "path": str(offers_path),
            "exists": False,
            "offers_count": 0,
            "comercializadoras_count": 0,
            "snapshot_date": None,
            "file_mtime": None,
        }
    offers: list[dict[str, Any]] = []
    with offers_path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if line:
                try:
                    offers.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    comercializadoras = {o.get("comercializadora") for o in offers if o.get("comercializadora")}
    snapshot_dates = {o.get("snapshot_date") for o in offers if o.get("snapshot_date")}
    return {
        "path": str(offers_path),
        "exists": True,
        "offers_count": len(offers),
        "comercializadoras_count": len(comercializadoras),
        "snapshot_date": sorted(snapshot_dates)[-1] if snapshot_dates else None,
        "file_mtime": offers_path.stat().st_mtime,
    }


@router.get("/registry", dependencies=[Depends(require_admin)])
async def registry_view(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
) -> dict[str, Any]:
    settings = request.app.state.settings
    registry_path = settings.artifact_dir / "registry" / "ofertas.jsonl"
    if not registry_path.exists():
        return {"path": str(registry_path), "exists": False, "total": 0, "patterns": []}
    patterns: list[dict[str, Any]] = []
    with registry_path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if line:
                try:
                    patterns.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return {
        "path": str(registry_path),
        "exists": True,
        "total": len(patterns),
        "patterns": patterns[-limit:],
    }
