from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from backend.app.offers.display import display_comercializadora
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


@router.get("/result/{run_id}")
async def result(
    run_id: str,
    request: Request,
    no_permanencia: bool = Query(default=False),
    only_verde: bool = Query(default=False),
    only_fijo: bool = Query(default=False),
    top_n: int = Query(default=10, ge=1, le=50),
) -> dict[str, Any]:
    cache = request.app.state.profile_cache
    cached = cache.get(run_id)
    if cached is None:
        raise HTTPException(status_code=404, detail="Result expired or not found")

    offers = request.app.state.offers_loader.all()
    constraints = Constraints(
        no_permanencia=no_permanencia,
        only_verde=only_verde,
        only_fijo=only_fijo,
    )
    user_total = cached.get("user_total_eur") or 0.0
    ranked = rank_offers(offers, float(user_total), constraints, top_n)

    masked = cached["masked_profile"]
    extracted_set = set(cached.get("extracted_fields") or [])

    return {
        "run_id": run_id,
        "filename": cached.get("filename"),
        "user_total_eur": user_total,
        "constraints": {
            "no_permanencia": no_permanencia,
            "only_verde": only_verde,
            "only_fijo": only_fijo,
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
        "ranked_offers": [
            {
                "rank": r.rank,
                "importe_primera_factura_eur": r.importe_eur,
                "savings_vs_user_eur": r.savings_vs_user_eur,
                "comercializadora": display_comercializadora(r.offer.get("comercializadora")),
                "oferta": r.offer.get("oferta"),
                "tipo_precio": r.offer.get("tipo_precio"),
                "verde": r.offer.get("verde"),
                "penalizacion": r.offer.get("penalizacion"),
                "descuento_promocional_eur": r.offer.get("descuento_promocional_eur"),
            }
            for r in ranked
        ],
    }
