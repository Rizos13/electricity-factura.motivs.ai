from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Constraints:
    no_permanencia: bool = False
    only_verde: bool = False
    only_fijo: bool = False


@dataclass(frozen=True)
class RankedOffer:
    rank: int
    offer: dict[str, Any]
    importe_eur: float
    savings_vs_user_eur: float


def rank_offers(
    offers: list[dict[str, Any]],
    user_total_eur: float,
    constraints: Constraints = Constraints(),
    top_n: int = 10,
) -> list[RankedOffer]:
    filtered = [o for o in offers if _passes_constraints(o, constraints)]
    scored: list[tuple[dict[str, Any], float]] = []
    for offer in filtered:
        importe = _to_float(offer.get("importe_primera_factura_eur"))
        if importe is not None:
            scored.append((offer, importe))
    scored.sort(key=lambda pair: pair[1])
    return [
        RankedOffer(
            rank=index + 1,
            offer=offer,
            importe_eur=importe,
            savings_vs_user_eur=round(user_total_eur - importe, 2),
        )
        for index, (offer, importe) in enumerate(scored[:top_n])
    ]


def _passes_constraints(offer: dict[str, Any], constraints: Constraints) -> bool:
    if constraints.no_permanencia and _as_str(offer.get("penalizacion")) == "si":
        return False
    if constraints.only_verde and _as_str(offer.get("verde")) != "si":
        return False
    if constraints.only_fijo and _as_str(offer.get("tipo_precio")) != "fijo":
        return False
    return True


def _as_str(value: Any) -> str:
    return str(value or "").strip().lower()


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
