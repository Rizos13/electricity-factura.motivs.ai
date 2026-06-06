from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from backend.app.offers.display import brand_tier, brand_url, display_comercializadora
from backend.app.tariff import TARIFF_2_0TD_2026, decompose_bill, estimate_offer_cost


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
    tariff = TARIFF_2_0TD_2026
    user_total = float(cached.get("user_total_eur") or 0.0)
    period_days = int(_to_float(masked.get("periodo_facturacion_dias")) or 30)
    user_kw = _to_float(masked.get("potencia_p1_kw")) or tariff.cnmc_ref_potencia_kw
    user_p1 = _to_float(masked.get("consumo_kwh_punta")) or 0.0
    user_p2 = _to_float(masked.get("consumo_kwh_llano")) or 0.0
    user_p3 = _to_float(masked.get("consumo_kwh_valle")) or 0.0

    user_breakdown = decompose_bill(
        total_eur=user_total,
        period_days=period_days,
        potencia_kw=user_kw,
        consumo_kwh_punta=user_p1,
        consumo_kwh_llano=user_p2,
        consumo_kwh_valle=user_p3,
        tariff=tariff,
    )
    user_monthly = user_breakdown.monthly_total_eur

    rendered = []
    for offer in offers:
        importe = _to_float(offer.get("importe_primera_factura_eur"))
        if importe is None:
            continue
        if only_verde and str(offer.get("verde") or "").strip().lower() != "si":
            continue
        cost = estimate_offer_cost(importe, user_kw, user_breakdown.annual_kwh, tariff)
        rendered.append(_render_offer(offer, cost, importe, user_monthly))
    rendered.sort(key=lambda o: o["importe_estimated_eur"])
    rendered = rendered[:top_n]
    for i, o in enumerate(rendered):
        o["rank"] = i + 1

    recommendation = _pick_recommendation(rendered)
    if recommendation and "total_factura_eur" in (cached.get("defaulted_fields") or []):
        recommendation = None

    extracted_set = set(cached.get("extracted_fields") or [])
    defaulted = set(cached.get("defaulted_fields") or [])
    critical = {"total_factura_eur", "consumo_kwh_punta", "consumo_kwh_llano", "consumo_kwh_valle"}
    critical_defaulted = critical & defaulted
    if "total_factura_eur" in critical_defaulted:
        quality = "low"
    elif critical_defaulted:
        quality = "medium"
    else:
        quality = "high"

    return {
        "run_id": run_id,
        "filename": cached.get("filename"),
        "extraction_quality": quality,
        "user_total_eur": user_total,
        "user_monthly_eur": user_monthly,
        "user_period_days": period_days,
        "user_annual_kwh": round(user_breakdown.annual_kwh, 0) if user_breakdown.annual_kwh else None,
        "user_potencia_kw": user_kw,
        "user_breakdown": {
            "monthly_potencia_eur": user_breakdown.monthly_potencia_eur,
            "monthly_energy_eur": user_breakdown.monthly_energy_eur,
            "monthly_fixed_eur": user_breakdown.monthly_fixed_eur,
            "monthly_taxes_eur": user_breakdown.monthly_taxes_eur,
            "effective_energy_eur_kwh": user_breakdown.effective_energy_eur_kwh,
        },
        "cnmc_default_annual_kwh": tariff.cnmc_ref_consumo_kwh_year,
        "cnmc_default_potencia_kw": tariff.cnmc_ref_potencia_kw,
        "cnmc_snapshot_date": snapshot_date,
        "tariff_label": tariff.label,
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


def _detect_snapshot_date(offers: list[dict[str, Any]]) -> str | None:
    for o in offers:
        date = o.get("snapshot_date")
        if date:
            return str(date)[:10]
    return None


def _render_offer(offer: dict[str, Any], cost: Any, importe: float, user_monthly: float) -> dict[str, Any]:
    raw_brand = offer.get("comercializadora")
    descuento = _to_float(offer.get("descuento_promocional_eur"))
    is_promo = bool(descuento and descuento > 0)
    tipo = offer.get("tipo_precio")
    savings = round(user_monthly - cost.monthly_total_eur, 2) if user_monthly else 0.0
    return {
        "rank": 0,
        "comercializadora": display_comercializadora(raw_brand),
        "brand_tier": brand_tier(raw_brand),
        "brand_url": brand_url(raw_brand),
        "oferta": offer.get("oferta"),
        "tipo_precio": tipo,
        "commitment_key": _commitment_key(tipo),
        "importe_cnmc_default_eur": importe,
        "importe_estimated_eur": cost.monthly_total_eur,
        "savings_vs_user_eur": savings,
        "offer_breakdown": {
            "monthly_potencia_eur": cost.monthly_potencia_eur,
            "monthly_energy_eur": cost.monthly_energy_eur,
            "monthly_fixed_eur": cost.monthly_fixed_eur,
            "monthly_taxes_eur": cost.monthly_taxes_eur,
            "effective_energy_eur_kwh": cost.offer_effective_energy_eur_kwh,
        },
        "is_promotional": is_promo,
        "descuento_promocional_eur": descuento,
        "verde": offer.get("verde"),
        "penalizacion": offer.get("penalizacion"),
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
                    "offer_breakdown": offer["offer_breakdown"],
                }
    return None


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
