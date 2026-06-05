from __future__ import annotations

import json
from collections import Counter
from typing import Any, Literal

from motivs_core import Pipeline, SyncPipeline, load_contract_yaml
from motivs_core.adapters.memory import (
    EnvSecrets,
    InMemoryRegistryStore,
    InMemoryRunRepository,
    InMemoryStorage,
)
from motivs_core.config import PipelineConfig

from backend.app.core.config import Settings
from backend.app.motivs.emitter import StructLogEmitter
from backend.app.motivs.registry_fs import FileSystemRegistryStore


ContractKind = Literal["factura", "ofertas"]


def _pipeline_kwargs(
    settings: Settings,
    kind: ContractKind,
    shadow_baseline_required: bool,
) -> tuple[dict[str, Any], InMemoryRunRepository]:
    contract_path = (
        settings.factura_contract_path if kind == "factura"
        else settings.ofertas_contract_path
    )
    contract = load_contract_yaml(contract_path.read_text())
    secrets = EnvSecrets({settings.tenant_slug: settings.hmac_key.encode()})
    repository = InMemoryRunRepository()
    if kind == "ofertas":
        registry_path = settings.artifact_dir / "registry" / "ofertas.jsonl"
        registry_store: Any = FileSystemRegistryStore(registry_path)
    else:
        registry_store = InMemoryRegistryStore()
    kwargs: dict[str, Any] = {
        "contract": contract,
        "repository": repository,
        "storage": InMemoryStorage(),
        "secrets": secrets,
        "emitter": StructLogEmitter(),
        "registry_store": registry_store,
        "config": PipelineConfig(
            tenant_slug=settings.tenant_slug,
            shadow_baseline_required=shadow_baseline_required,
        ),
    }
    return kwargs, repository


def build_pipeline(
    settings: Settings,
    kind: ContractKind,
    *,
    shadow_baseline_required: bool = False,
) -> tuple[SyncPipeline, InMemoryRunRepository]:
    kwargs, repository = _pipeline_kwargs(settings, kind, shadow_baseline_required)
    return SyncPipeline(**kwargs), repository


def build_async_pipeline(
    settings: Settings,
    kind: ContractKind,
    *,
    shadow_baseline_required: bool = False,
) -> tuple[Pipeline, InMemoryRunRepository]:
    kwargs, repository = _pipeline_kwargs(settings, kind, shadow_baseline_required)
    return Pipeline(**kwargs), repository


def dump_state(
    repository: InMemoryRunRepository,
    settings: Settings,
    *,
    kind: ContractKind | None = None,
) -> dict[str, Any]:
    """Append in-memory runs to motivs_runs.jsonl, rebuild summary from history."""
    runs_path = settings.motivs_runs_path
    summary_path = settings.motivs_summary_path
    runs_path.parent.mkdir(parents=True, exist_ok=True)

    runs = list(repository._runs.values())
    events_by_run = dict(repository._events)

    with runs_path.open("a", encoding="utf-8") as fh:
        for run in runs:
            entry = {
                "run_id": run["id"],
                "kind": kind,
                "status": run["status"],
                "verdict": run["verdict"],
                "score": run["score"],
                "started_at": _iso(run.get("started_at")),
                "finished_at": _iso(run.get("finished_at")),
                "contract_version": run["contract_version"],
                "input_hash": run["input_hash"],
                "events": events_by_run.get(run["id"], []),
            }
            fh.write(json.dumps(entry, default=str) + "\n")

    return _rebuild_summary(runs_path, summary_path)


def _rebuild_summary(runs_path, summary_path) -> dict[str, Any]:
    verdict_counts: Counter[str] = Counter()
    module_decisions: Counter[str] = Counter()
    kind_counts: Counter[str] = Counter()
    total = 0
    last_run_id: str | None = None
    last_kind: str | None = None
    last_contract_version: str | None = None

    if runs_path.exists():
        with runs_path.open("r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                total += 1
                verdict = entry.get("verdict") or (entry.get("status") or "").upper()
                if verdict:
                    verdict_counts[verdict] += 1
                if entry.get("kind"):
                    kind_counts[entry["kind"]] += 1
                for event in entry.get("events", []):
                    module = event.get("module") or "?"
                    decision = event.get("decision") or "?"
                    module_decisions[f"{module}:{decision}"] += 1
                last_run_id = entry.get("run_id")
                last_kind = entry.get("kind")
                last_contract_version = entry.get("contract_version")

    summary = {
        "total_runs": total,
        "verdicts": dict(verdict_counts),
        "module_decisions": dict(module_decisions),
        "kind_counts": dict(kind_counts),
        "last_run_id": last_run_id,
        "last_kind": last_kind,
        "contract_version": last_contract_version,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2))
    return summary


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
