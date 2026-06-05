from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from backend.app.offers.display import brand_tier, brand_url, display_comercializadora
from backend.app.ranker.rank import Constraints, rank_offers


router = APIRouter(prefix="/api", tags=["result"])


_PII_DROPPED_FIELDS = ("nombre_titular", "direccion_suministro", "num_factura", "num_contrato")
_PII_HASHED_FIELDS = ("cups", "nif", "iban")
_PROFILE_VISIBLE_FIELDS = (
    "comercializadora_actual",
    "tarifa_acceso",
    "region",
    "codigo_postal",
    "potencia_p1_kw",
    "consumo_kwh_punta",
    "consumo_kwh_llano",
    "consumo_kwh_valle",
    "total_factura_eur",
    "periodo_facturacion_dias",
)
_KNOWN_BRAND_TIERS = ("major", "regulated")
_CNMC_DEFAULT_ANNUAL_KWH = 3500.0


@router.get("/result/{run_id}")
async def result(
    run_id: str,
    request: Request,
    solo_marcas_conocidas: bool = Query(default=True),
    only_verde: bool = Query(default=False),
    top_n: int = Query(default=10, ge=1, le=50),
) -> dict[str, Any]:
    cache = request.app.state.profile_cache
    cached = cache.get(run_id)
    if cached is None:
        raise HTTPException(status_code=404, detail="Result expired or not found")

    offers = request.app.state.offers_loader.all()
    snapshot_date = _detect_snapshot_date(offers)

    if solo_marcas_conocidas:
        offers = [o for o in offers if brand_tier(o.get("comercializadora")) in _KNOWN_BRAND_TIERS]

    masked = cached["masked_profile"]
    user_total = float(cached.get("user_total_eur") or 0.0)
    user_annual_kwh = _user_annual_kwh(masked)
    scaling_factor = (
        user_annual_kwh / _CNMC_DEFAULT_ANNUAL_KWH if user_annual_kwh > 0 else 1.0
    )

    ranked = rank_offers(offers, user_total, Constraints(only_verde=only_verde), top_n)
    rendered = [_render_offer(r, scaling_factor, user_total) for r in ranked]
    recommendation = _pick_recommendation(rendered)

    extracted_set = set(cached.get("extracted_fields") or [])

    return {
        "run_id": run_id,
        "filename": cached.get("filename"),
        "user_total_eur": user_total,
        "user_annual_kwh": round(user_annual_kwh, 0) if user_annual_kwh else None,
        "cnmc_default_annual_kwh": _CNMC_DEFAULT_ANNUAL_KWH,
        "cnmc_snapshot_date": snapshot_date,
        "scaling_factor": round(scaling_factor, 3),
        "constraints": {
            "solo_marcas_conocidas": solo_marcas_conocidas,
            "only_verde": only_verde,
        },
        "extraction": {
            "extracted_fields_count": len(extracted_set),
            "defaulted_fields": cached.get("defaulted_fields") or [],
            "ocr_used": cached.get("ocr_used", False),
        },
        "masking": {
            "dropped": [f for f in _PII_DROPPED_FIELDS if f in extracted_set],
            "hashed": [f for f in _PII_HASHED_FIELDS if f in extracted_set],
        },
        "profile_summary": {f: masked.get(f) for f in _PROFILE_VISIBLE_FIELDS},
        "recommendation": recommendation,
        "ranked_offers": rendered,
    }


def _user_annual_kwh(masked: dict[str, Any]) -> float:
    punta = _to_float(masked.get("consumo_kwh_punta")) or 0
    llano = _to_float(masked.get("consumo_kwh_llano")) or 0
    valle = _to_float(masked.get("consumo_kwh_valle")) or 0
    period_days = _to_float(masked.get("periodo_facturacion_dias")) or 0
    if period_days <= 0:
        return 0.0
    return (punta + llano + valle) * (365.0 / period_days)


def _detect_snapshot_date(offers: list[dict[str, Any]]) -> str | None:
    for o in offers:
        date = o.get("snapshot_date")
        if date:
            return str(date)[:10]
    return None


def _render_offer(r: Any, scaling_factor: float, user_total: float) -> dict[str, Any]:
    raw_brand = r.offer.get("comercializadora")
    descuento = _to_float(r.offer.get("descuento_promocional_eur"))
    is_promo = bool(descuento and descuento > 0)
    tipo = r.offer.get("tipo_precio")
    scaled = round(r.importe_eur * scaling_factor, 2) if scaling_factor else r.importe_eur
    savings_scaled = round(user_total - scaled, 2) if user_total else 0.0
    return {
        "rank": r.rank,
        "comercializadora": display_comercializadora(raw_brand),
        "brand_tier": brand_tier(raw_brand),
        "brand_url": brand_url(raw_brand),
        "oferta": r.offer.get("oferta"),
        "tipo_precio": tipo,
        "commitment_key": _commitment_key(tipo),
        "importe_cnmc_default_eur": r.importe_eur,
        "importe_estimated_eur": scaled,
        "savings_vs_user_eur": savings_scaled,
        "is_promotional": is_promo,
        "descuento_promocional_eur": descuento,
        "verde": r.offer.get("verde"),
        "penalizacion": r.offer.get("penalizacion"),
    }


def _commitment_key(tipo: str | None) -> str:
    if tipo == "fijo":
        return "commitment_fijo"
    if tipo == "pvpc":
        return "commitment_pvpc"
    if tipo == "flexible":
        return "commitment_flexible"
    return "commitment_unknown"


def _pick_recommendation(rendered: list[dict[str, Any]]) -> dict[str, Any] | None:
    for predicate, key in (
        (lambda o: o["brand_tier"] == "major" and not o["is_promotional"] and o["tipo_precio"] == "fijo", "rec_reason_major_fijo"),
        (lambda o: not o["is_promotional"], "rec_reason_cheapest_clean"),
    ):
        for offer in rendered:
            if predicate(offer):
                savings = offer["savings_vs_user_eur"] or 0
                return {
                    "comercializadora": offer["comercializadora"],
                    "brand_url": offer["brand_url"],
                    "importe_estimated_eur": offer["importe_estimated_eur"],
                    "importe_cnmc_default_eur": offer["importe_cnmc_default_eur"],
                    "savings_vs_user_eur": savings,
                    "savings_annual_eur": round(savings * 12, 2),
                    "oferta": offer["oferta"],
                    "rationale_key": key,
                }
    return None


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
