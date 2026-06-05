from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from motivs_core import SyncPipeline, Verdict
from motivs_core.types import StepResult


_pending: dict[str, dict[str, Any]] = {}


@dataclass
class GateResult:
    verdict: str
    passed: bool
    events: list[dict[str, Any]]
    output_rows: list[dict[str, Any]] | None
    run_id: str | None


def check(pipeline: SyncPipeline, file_bytes: bytes, file_name: str) -> GateResult:
    result = pipeline.run(file_bytes=file_bytes, file_name=file_name)

    if result.verdict == Verdict.AWAITING_APPROVAL and result.run_id:
        shadow = next((ev for ev in result.events if ev.module == "shadow-run"), None)
        if shadow is not None:
            _pending[result.run_id] = {
                "prior_events": list(result.events),
                "shadow_result": shadow,
                "file_bytes": file_bytes,
                "file_name": file_name,
            }

    return GateResult(
        verdict=result.verdict.value,
        passed=result.verdict == Verdict.DELIVERED,
        events=_serialize_events(result.events),
        output_rows=result.output_rows,
        run_id=result.run_id,
    )


def approve_shadow(
    pipeline: SyncPipeline,
    run_id: str,
    approver: str = "operator",
) -> GateResult | None:
    pending = _pending.pop(run_id, None)
    if pending is None:
        return None
    result, _ = pipeline.resume(
        run_id=run_id,
        prior_events=pending["prior_events"],
        shadow_result=pending["shadow_result"],
        approver=approver,
        file_bytes=pending["file_bytes"],
        file_name=pending["file_name"],
    )
    return GateResult(
        verdict=result.verdict.value,
        passed=result.verdict == Verdict.DELIVERED,
        events=_serialize_events(result.events),
        output_rows=result.output_rows,
        run_id=result.run_id,
    )


def _serialize_events(events: list[StepResult]) -> list[dict[str, Any]]:
    return [
        {
            "module": ev.module,
            "decision": ev.decision.value,
            "score": ev.score,
            "duration_ms": ev.duration_ms,
            "reasoning": ev.reasoning,
            "signals": [
                {
                    "key": s.key,
                    "value": s.value,
                    "severity": s.severity.value,
                    "note": s.note or "",
                }
                for s in ev.signals
            ],
        }
        for ev in events
    ]
