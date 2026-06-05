from __future__ import annotations

import pytest

from backend.app.ranker.rank import Constraints, RankedOffer, rank_offers


def _make_offer(
    *,
    offer_id: str,
    importe: float,
    tipo: str = "fijo",
    verde: str = "no",
    pen: str = "no",
) -> dict:
    return {
        "offer_id": offer_id,
        "comercializadora": "ACME",
        "oferta": offer_id,
        "tipo_precio": tipo,
        "importe_primera_factura_eur": importe,
        "verde": verde,
        "penalizacion": pen,
    }


@pytest.fixture
def offers() -> list[dict]:
    return [
        _make_offer(offer_id="cheap_verde", importe=40.00, verde="si", pen="no"),
        _make_offer(offer_id="cheap_nonverde", importe=42.50, verde="no", pen="no"),
        _make_offer(offer_id="mid_perm", importe=50.00, verde="si", pen="si"),
        _make_offer(offer_id="mid_flex", importe=55.00, tipo="flexible", verde="si"),
        _make_offer(offer_id="expensive_fijo", importe=100.00, tipo="fijo"),
    ]


def test_sort_ascending_by_importe(offers):
    top = rank_offers(offers, user_total_eur=200.0, top_n=10)
    assert [r.offer["offer_id"] for r in top] == [
        "cheap_verde",
        "cheap_nonverde",
        "mid_perm",
        "mid_flex",
        "expensive_fijo",
    ]


def test_savings_calculation(offers):
    top = rank_offers(offers, user_total_eur=100.0, top_n=2)
    assert top[0].savings_vs_user_eur == pytest.approx(60.0)
    assert top[1].savings_vs_user_eur == pytest.approx(57.5)


def test_negative_savings_when_offer_is_higher(offers):
    top = rank_offers(offers, user_total_eur=30.0, top_n=1)
    assert top[0].savings_vs_user_eur == pytest.approx(-10.0)


def test_constraint_only_verde(offers):
    top = rank_offers(offers, user_total_eur=200.0, constraints=Constraints(only_verde=True))
    ids = [r.offer["offer_id"] for r in top]
    assert "cheap_nonverde" not in ids
    assert "expensive_fijo" not in ids
    assert ids == ["cheap_verde", "mid_perm", "mid_flex"]


def test_constraint_no_permanencia(offers):
    top = rank_offers(offers, user_total_eur=200.0, constraints=Constraints(no_permanencia=True))
    ids = [r.offer["offer_id"] for r in top]
    assert "mid_perm" not in ids


def test_constraint_only_fijo(offers):
    top = rank_offers(offers, user_total_eur=200.0, constraints=Constraints(only_fijo=True))
    ids = [r.offer["offer_id"] for r in top]
    assert "mid_flex" not in ids


def test_top_n_truncates(offers):
    top = rank_offers(offers, user_total_eur=200.0, top_n=2)
    assert len(top) == 2


def test_rank_starts_at_one(offers):
    top = rank_offers(offers, user_total_eur=200.0, top_n=3)
    assert [r.rank for r in top] == [1, 2, 3]


def test_missing_importe_is_skipped(offers):
    offers.append(_make_offer(offer_id="no_price", importe=None))  # type: ignore[arg-type]
    offers[-1]["importe_primera_factura_eur"] = None
    top = rank_offers(offers, user_total_eur=200.0)
    assert all(r.offer["offer_id"] != "no_price" for r in top)


def test_returns_ranked_offer_dataclass(offers):
    top = rank_offers(offers, user_total_eur=200.0, top_n=1)
    assert isinstance(top[0], RankedOffer)
