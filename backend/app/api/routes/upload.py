from __future__ import annotations

import csv
import io
import logging
from typing import Any

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from motivs_core import Verdict
from pydantic import BaseModel

from backend.app.factura.extractor import ExtractResult, extract_factura
from backend.app.motivs.factory import build_async_pipeline, dump_state


router = APIRouter(prefix="/api", tags=["upload"])
logger = logging.getLogger(__name__)

_MAX_UPLOAD_BYTES = 8 * 1024 * 1024
_SUPPORTED_EXTENSIONS = (".pdf", ".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff")
_CONTRACT_FIELDS = (
    "cups",
    "nif",
    "nombre_titular",
    "direccion_suministro",
    "iban",
    "num_factura",
    "num_contrato",
    "comercializadora_actual",
    "distribuidora",
    "codigo_postal",
    "region",
    "tarifa_acceso",
    "potencia_p1_kw",
    "potencia_p2_kw",
    "consumo_kwh_punta",
    "consumo_kwh_llano",
    "consumo_kwh_valle",
    "precio_kwh_actual_p1",
    "precio_kwh_actual_p2",
    "precio_kwh_actual_p3",
    "termino_potencia_eur_dia",
    "permanencia_actual_meses",
    "periodo_facturacion_dias",
    "total_factura_eur",
    "ocr_text",
)


class UploadResponse(BaseModel):
    run_id: str
    verdict: str
    ocr_used: bool
    extracted_fields: list[str]
    defaulted_fields: list[str]
    filename: str


@router.post("/upload", response_model=UploadResponse)
async def upload(request: Request, file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    if not file.filename.lower().endswith(_SUPPORTED_EXTENSIONS):
        raise HTTPException(status_code=400, detail="Only PDF or image uploads are accepted")
    data = await file.read()
    if len(data) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 8 MB)")

    try:
        extract = extract_factura(data, file.filename)
    except Exception as exc:
        logger.exception("factura_extract_failed", extra={"upload_filename": file.filename})
        raise HTTPException(
            status_code=422,
            detail="We could not read this bill. Please upload a valid electricity bill PDF or image.",
        ) from exc

    settings = request.app.state.settings
    pipeline, repository = build_async_pipeline(settings, kind="factura", shadow_baseline_required=False)
    csv_bytes = _record_to_csv(extract.record)
    result = await pipeline.run(file_bytes=csv_bytes, file_name=file.filename + ".csv")
    dump_state(repository, settings, kind="factura")

    if result.verdict == Verdict.QUARANTINED:
        raise HTTPException(
            status_code=422,
            detail="The bill could not be processed safely. Please try a different file.",
        )
    if result.verdict == Verdict.AWAITING_APPROVAL:
        raise HTTPException(
            status_code=425,
            detail="The bill format is new to us. An operator must approve it before results are available.",
        )
    if result.verdict != Verdict.DELIVERED or not result.output_rows:
        raise HTTPException(status_code=500, detail="Unexpected pipeline verdict")
    if not result.run_id:
        raise HTTPException(status_code=500, detail="Pipeline did not return a run id")

    masked_profile = result.output_rows[0]
    cache = request.app.state.profile_cache
    cache.put(
        result.run_id,
        {
            "masked_profile": masked_profile,
            "user_total_eur": _to_float(masked_profile.get("total_factura_eur")),
            "extracted_fields": extract.extracted_fields,
            "defaulted_fields": extract.defaulted_fields,
            "ocr_used": extract.ocr_used,
            "filename": file.filename,
        },
    )

    return UploadResponse(
        run_id=result.run_id,
        verdict=result.verdict.value,
        ocr_used=extract.ocr_used,
        extracted_fields=extract.extracted_fields,
        defaulted_fields=extract.defaulted_fields,
        filename=file.filename,
    )


def _record_to_csv(record: dict[str, Any]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(_CONTRACT_FIELDS), quoting=csv.QUOTE_ALL)
    writer.writeheader()
    writer.writerow({
        field: ("" if record.get(field) is None else record[field])
        for field in _CONTRACT_FIELDS
    })
    return buf.getvalue().encode("utf-8")


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
