from __future__ import annotations

import time

from backend.app.services.ttl_cache import TTLCache


def test_put_and_get_round_trip():
    cache = TTLCache(default_ttl_seconds=60)
    cache.put("k1", {"v": 1})
    assert cache.get("k1") == {"v": 1}


def test_get_missing_returns_none():
    cache = TTLCache(default_ttl_seconds=60)
    assert cache.get("missing") is None


def test_entry_expires_after_ttl():
    cache = TTLCache(default_ttl_seconds=60)
    cache.put("short", "value", ttl_seconds=0)
    time.sleep(0.01)
    assert cache.get("short") is None


def test_delete_removes_entry():
    cache = TTLCache(default_ttl_seconds=60)
    cache.put("k", 1)
    cache.delete("k")
    assert cache.get("k") is None


def test_sweep_removes_expired_only():
    cache = TTLCache(default_ttl_seconds=60)
    cache.put("alive", "x", ttl_seconds=60)
    cache.put("dead", "y", ttl_seconds=0)
    time.sleep(0.01)
    removed = cache.sweep()
    assert removed == 1
    assert cache.get("alive") == "x"
    assert cache.get("dead") is None


def test_overrides_existing_key():
    cache = TTLCache(default_ttl_seconds=60)
    cache.put("k", "first")
    cache.put("k", "second")
    assert cache.get("k") == "second"


def test_len_reflects_store_size():
    cache = TTLCache(default_ttl_seconds=60)
    cache.put("a", 1)
    cache.put("b", 2)
    assert len(cache) == 2
