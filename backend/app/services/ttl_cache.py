from __future__ import annotations

import threading
import time
from typing import Any


class TTLCache:
    """Process-local key-value store with per-entry expiry."""

    def __init__(self, default_ttl_seconds: int) -> None:
        self._default_ttl = default_ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def put(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        expires_at = time.monotonic() + ttl
        with self._lock:
            self._store[key] = (expires_at, value)

    def get(self, key: str) -> Any | None:
        now = time.monotonic()
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at <= now:
                del self._store[key]
                return None
            return value

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def sweep(self) -> int:
        now = time.monotonic()
        with self._lock:
            expired = [k for k, (exp, _) in self._store.items() if exp <= now]
            for k in expired:
                del self._store[k]
            return len(expired)

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)
