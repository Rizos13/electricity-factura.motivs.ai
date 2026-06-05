from __future__ import annotations

import asyncio
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class FileSystemRegistryStore:
    """RegistryStore backed by a single jsonl file, atomic rewrites."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = asyncio.Lock()
        self._patterns: list[dict[str, Any]] = self._read_from_disk()

    def _read_from_disk(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        patterns: list[dict[str, Any]] = []
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    patterns.append(json.loads(line))
        return patterns

    def _persist(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self._path.parent,
            delete=False,
            suffix=".tmp",
        ) as tmp:
            for pattern in self._patterns:
                tmp.write(json.dumps(pattern, separators=(",", ":")) + "\n")
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = tmp.name
        os.replace(tmp_path, self._path)

    async def load_patterns(self, contract_version: str) -> list[dict[str, Any]]:
        async with self._lock:
            return [dict(p) for p in self._patterns]

    async def save_pattern(self, pattern: dict[str, Any]) -> None:
        async with self._lock:
            self._patterns.append(dict(pattern))
            self._persist()

    async def record_match(self, pattern_id: str) -> int:
        async with self._lock:
            for p in self._patterns:
                if p.get("id") == pattern_id:
                    p["times_seen"] = int(p.get("times_seen", 0)) + 1
                    p["last_seen_at"] = datetime.now(timezone.utc).isoformat()
                    self._persist()
                    return int(p["times_seen"])
            return 0
