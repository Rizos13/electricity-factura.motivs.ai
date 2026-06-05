from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class OffersLoader:
    """In-memory cache of delivered ofertas from a jsonl artifact."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._offers: list[dict[str, Any]] = []
        self._loaded = False

    def reload(self) -> int:
        if not self._path.exists():
            self._offers = []
            self._loaded = True
            return 0
        offers: list[dict[str, Any]] = []
        with self._path.open("r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if line:
                    offers.append(json.loads(line))
        self._offers = offers
        self._loaded = True
        return len(offers)

    def all(self) -> list[dict[str, Any]]:
        if not self._loaded:
            self.reload()
        return [dict(o) for o in self._offers]

    def count(self) -> int:
        if not self._loaded:
            self.reload()
        return len(self._offers)

    @property
    def path(self) -> Path:
        return self._path
