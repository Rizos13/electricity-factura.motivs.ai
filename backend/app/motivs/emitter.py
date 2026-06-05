from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger("motivs")


class StructLogEmitter:
    """Emits motivs gate events into the json structured log."""

    async def emit(self, run_id: str, event: Any) -> None:
        self._log(run_id, event)

    def emit_sync(self, run_id: str, event: Any) -> None:
        self._log(run_id, event)

    @staticmethod
    def _log(run_id: str, event: Any) -> None:
        logger.info(
            "motivs_event",
            extra={
                "run_id": run_id,
                "motivs_module": getattr(event, "module", None),
                "decision": getattr(getattr(event, "decision", None), "value", None),
                "event_score": getattr(event, "score", None),
            },
        )
