from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.motivs.registry_fs import FileSystemRegistryStore


@pytest.mark.asyncio
async def test_save_and_load_round_trip(tmp_path: Path) -> None:
    store = FileSystemRegistryStore(tmp_path / "registry.jsonl")
    await store.save_pattern({"id": "p1", "signature_hash": "abc", "decision": "ACCEPT"})
    await store.save_pattern({"id": "p2", "signature_hash": "def", "decision": "BLOCK"})

    fresh = FileSystemRegistryStore(tmp_path / "registry.jsonl")
    patterns = await fresh.load_patterns(contract_version="1.0")

    assert [p["id"] for p in patterns] == ["p1", "p2"]
    assert patterns[1]["decision"] == "BLOCK"


@pytest.mark.asyncio
async def test_record_match_increments_and_persists(tmp_path: Path) -> None:
    path = tmp_path / "registry.jsonl"
    store = FileSystemRegistryStore(path)
    await store.save_pattern({"id": "p1", "times_seen": 0})

    new_count = await store.record_match("p1")
    assert new_count == 1

    again = await store.record_match("p1")
    assert again == 2

    on_disk = [json.loads(line) for line in path.read_text().splitlines() if line]
    assert on_disk[0]["times_seen"] == 2
    assert "last_seen_at" in on_disk[0]


@pytest.mark.asyncio
async def test_record_match_unknown_returns_zero(tmp_path: Path) -> None:
    store = FileSystemRegistryStore(tmp_path / "registry.jsonl")
    assert await store.record_match("missing") == 0


@pytest.mark.asyncio
async def test_load_from_empty_path(tmp_path: Path) -> None:
    store = FileSystemRegistryStore(tmp_path / "nonexistent.jsonl")
    assert await store.load_patterns(contract_version="1.0") == []
