from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.cnmc.parser import parse_cnmc_pdf


SNAPSHOT_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "cnmc_snapshots"
    / "cnmc_default_profile_2026-06-05.pdf"
)


@pytest.fixture(scope="module")
def offers() -> list[dict]:
    return parse_cnmc_pdf(SNAPSHOT_PATH.read_bytes())


def test_parses_at_least_forty_offers(offers: list[dict]) -> None:
    assert len(offers) >= 40


def test_snapshot_date_is_extracted(offers: list[dict]) -> None:
    assert all(o["snapshot_date"] == "2026-06-05" for o in offers)


def test_pvpc_entry_present(offers: list[dict]) -> None:
    pvpc = [o for o in offers if o["tipo_precio"] == "pvpc"]
    assert len(pvpc) >= 1
    assert pvpc[0]["importe_primera_factura_eur"] > 0


def test_known_comercializadoras_present(offers: list[dict]) -> None:
    names = {o["comercializadora"].upper() for o in offers}
    expected = {"IBERDROLA CLIENTES, S.A.U.", "ENDESA ENERGÍA S.A.U."}
    assert expected.issubset(names), names - expected


def test_required_fields_populated(offers: list[dict]) -> None:
    for o in offers:
        assert o["offer_id"]
        assert o["comercializadora"]
        assert o["oferta"]
        assert o["tipo_precio"] in {"fijo", "flexible", "pvpc"}
        assert o["importe_primera_factura_eur"] is not None
        assert o["penalizacion"] in {"si", "no"}
        assert o["verde"] in {"si", "no"}


def test_importes_in_realistic_range(offers: list[dict]) -> None:
    importes = [o["importe_primera_factura_eur"] for o in offers]
    assert min(importes) >= 10
    assert max(importes) <= 500


def test_offer_ids_are_unique(offers: list[dict]) -> None:
    ids = [o["offer_id"] for o in offers]
    assert len(set(ids)) == len(ids)
