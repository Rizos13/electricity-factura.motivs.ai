from __future__ import annotations

import io
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pdfplumber
from PIL import Image


_CUPS_RE = re.compile(r"\bES[0-9]{16}[A-Z]{2}[0-9A-Z]{0,2}\b")
_NIF_RE = re.compile(r"\b([XYZ]?[0-9]{7,8}[A-Z])\b")
_IBAN_RE = re.compile(r"\b(ES[0-9]{2}[\s0-9*]{20,30})\b")
_EUR_RE = re.compile(r"([0-9]{1,5}[.,][0-9]{2})\s*€")
_POSTAL_RE = re.compile(r"\b([0-4][0-9]{4}|5[0-2][0-9]{3})\b")
_TARIFA_RE = re.compile(r"\b([23]\.[01]TD)\b", re.IGNORECASE)
_POTENCIA_RE = re.compile(r"Potencia\s+P1\s*[:=]?\s*([0-9]+[.,]?[0-9]*)", re.IGNORECASE)
_CONSUMOS_RE = re.compile(
    r"consumos\s+han\s+sido\s+punta:\s*([0-9]+[.,]?[0-9]*)\s*kWh,\s*llano:\s*([0-9]+[.,]?[0-9]*)\s*kWh,\s*valle:\s*([0-9]+[.,]?[0-9]*)\s*kWh",
    re.IGNORECASE,
)
_PUNTA_RE = re.compile(r"punta\s*[:=]?\s*([0-9]+[.,]?[0-9]*)\s*kWh", re.IGNORECASE)
_LLANO_RE = re.compile(r"llano\s*[:=]?\s*([0-9]+[.,]?[0-9]*)\s*kWh", re.IGNORECASE)
_VALLE_RE = re.compile(r"valle\s*[:=]?\s*([0-9]+[.,]?[0-9]*)\s*kWh", re.IGNORECASE)
_TOTAL_PAY_RE = re.compile(r"pagar\?\s*([0-9]+[.,][0-9]+)\s*€", re.IGNORECASE)
_TOTAL_ELEC_RE = re.compile(r"Total\s+electricidad\s+([0-9]+[.,][0-9]+)", re.IGNORECASE)
_HOLA_RE = re.compile(r"Hola,?\s+([A-Z][\w\u00c0-\u017f]+(?:\s+[A-Z][\w\u00c0-\u017f]+)?)")
_CLIENT_RE = re.compile(r"Cliente:\s*([A-Z][^\n]{2,80})", re.IGNORECASE)
_DIRECCION_RE = re.compile(r"(?:Direcci[oó]n\s+del\s+suministro|Domicilio\s+cliente)\s*:\s*([^\n]{5,120})", re.IGNORECASE)
_NUM_FACTURA_RE = re.compile(r"Factura\s+electricidad\s+n[ºo°]\s*([A-Z0-9]{8,32})", re.IGNORECASE)
_NUM_CONTRATO_RE = re.compile(r"N[ºo°]\s+Cuenta\s+Contrato\s*:\s*([0-9]{6,20})", re.IGNORECASE)
_DISTRIBUIDORA_RE = re.compile(r"Distribuidora\s*:\s*([^\n;]{3,80})", re.IGNORECASE)
_PERIOD_RE = re.compile(r"([0-9]{2}\.[0-9]{2}\.[0-9]{4})\s*[-–]\s*([0-9]{2}\.[0-9]{2}\.[0-9]{4})")
_COMERCIALIZADORA_KEYWORDS = (
    "TOTALENERGIES", "MASMOVIL", "ENDESA", "IBERDROLA", "NATURGY", "REPSOL",
    "HOLALUZ", "OCTOPUS", "ENERGYA VM", "EDP", "ENI PLENITUDE", "FENIE",
    "WEKIWI", "NIBA", "IMAGINA", "DAIMUZ", "GAOLANIA", "CATGAS", "LUMISA",
    "ENERGIA NUFRI", "CIDE HC", "DOMESTICA", "TELECOR", "ENERGYASSET",
)
_REGION_BY_POSTAL_PREFIX = {
    "08": "barcelona",
    "17": "girona",
    "25": "lleida",
    "43": "tarragona",
}


@dataclass
class ExtractResult:
    record: dict[str, Any]
    extracted_fields: list[str]
    defaulted_fields: list[str]
    raw_text_preview: str
    ocr_used: bool


def extract_factura(file_bytes: bytes, filename: str) -> ExtractResult:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        text = _extract_text_pdf(file_bytes)
        ocr_used = False
    elif lower.endswith((".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff")):
        text = _extract_text_image(file_bytes)
        ocr_used = True
    else:
        raise ValueError(f"Unsupported file type: {filename}")
    return _parse_text(text, ocr_used)


def _extract_text_pdf(file_bytes: bytes) -> str:
    chunks: list[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            chunks.append(page.extract_text() or "")
    return "\n".join(chunks)


def _extract_text_image(file_bytes: bytes) -> str:
    import pytesseract

    image = Image.open(io.BytesIO(file_bytes))
    return pytesseract.image_to_string(image, lang="spa+eng", config="--psm 6")


def _parse_text(text: str, ocr_used: bool) -> ExtractResult:
    extracted: dict[str, Any] = {}
    fields: list[str] = []

    _try(extracted, fields, "comercializadora_actual", _find_comercializadora(text))
    _try(extracted, fields, "cups", _first_match(_CUPS_RE, text))
    _try(extracted, fields, "nif", _find_nif(text))
    _try(extracted, fields, "iban", _find_iban(text))
    _try(extracted, fields, "num_factura", _first_group(_NUM_FACTURA_RE, text))
    _try(extracted, fields, "num_contrato", _first_group(_NUM_CONTRATO_RE, text))
    _try(extracted, fields, "nombre_titular", _find_name(text))
    _try(extracted, fields, "direccion_suministro", _clean_address(_first_group(_DIRECCION_RE, text)))
    _try(extracted, fields, "distribuidora", _first_group(_DISTRIBUIDORA_RE, text))
    _try(extracted, fields, "tarifa_acceso", _find_tarifa(text))

    postal = _find_postal(text)
    if postal:
        extracted["codigo_postal"] = postal
        fields.append("codigo_postal")
        region = _REGION_BY_POSTAL_PREFIX.get(postal[:2])
        if region:
            extracted["region"] = region
            fields.append("region")

    _try_float(extracted, fields, "potencia_p1_kw", _first_group(_POTENCIA_RE, text))

    punta, llano, valle = _find_consumos(text)
    _try_float(extracted, fields, "consumo_kwh_punta", punta)
    _try_float(extracted, fields, "consumo_kwh_llano", llano)
    _try_float(extracted, fields, "consumo_kwh_valle", valle)

    total_eur = _find_total(text)
    if total_eur is not None:
        extracted["total_factura_eur"] = total_eur
        fields.append("total_factura_eur")

    period_days = _find_period_days(text)
    if period_days is not None:
        extracted["periodo_facturacion_dias"] = period_days
        fields.append("periodo_facturacion_dias")

    defaulted = _fill_defaults(extracted)
    extracted["ocr_text"] = text[:200_000]

    return ExtractResult(
        record=extracted,
        extracted_fields=sorted(set(fields)),
        defaulted_fields=sorted(set(defaulted)),
        raw_text_preview=text[:600],
        ocr_used=ocr_used,
    )


def _try(record: dict, fields: list, key: str, value: Any) -> None:
    if value:
        record[key] = value
        fields.append(key)


def _try_float(record: dict, fields: list, key: str, value: str | None) -> None:
    parsed = _to_float(value)
    if parsed is not None:
        record[key] = parsed
        fields.append(key)


def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    m = pattern.search(text)
    return m.group(0) if m else None


def _first_group(pattern: re.Pattern[str], text: str) -> str | None:
    m = pattern.search(text)
    return m.group(1).strip() if m else None


def _find_comercializadora(text: str) -> str | None:
    upper = text.upper()
    for name in _COMERCIALIZADORAS_BY_LENGTH():
        if name in upper:
            return name.title().replace("Hc", "HC")
    return None


def _COMERCIALIZADORAS_BY_LENGTH() -> tuple[str, ...]:
    return tuple(sorted(_COMERCIALIZADORA_KEYWORDS, key=len, reverse=True))


def _find_nif(text: str) -> str | None:
    for match in _NIF_RE.finditer(text):
        candidate = match.group(1)
        if len(candidate) >= 9 and not candidate.startswith("0"):
            return candidate
    return None


def _find_iban(text: str) -> str | None:
    m = _IBAN_RE.search(text)
    if not m:
        return None
    return re.sub(r"\s+", "", m.group(1))


def _find_name(text: str) -> str | None:
    m = _CLIENT_RE.search(text)
    if m:
        return _clean_name(m.group(1))
    m = _HOLA_RE.search(text)
    if m:
        return _clean_name(m.group(1))
    return None


def _clean_name(raw: str) -> str:
    # strip trailing tokens after CIF, NIF, anything in caps
    stop_tokens = ("CIF", "NIF", "DNI", "Tu", "TU", "tu")
    name = raw.strip()
    for token in stop_tokens:
        idx = name.find(f" {token}")
        if idx > 0:
            name = name[:idx]
    return name.strip(" ,:.")


def _find_postal(text: str) -> str | None:
    catalonia_match = None
    for m in _POSTAL_RE.finditer(text):
        code = m.group(0)
        if code[:2] in _REGION_BY_POSTAL_PREFIX:
            catalonia_match = code
            break
    return catalonia_match or _first_match(_POSTAL_RE, text)


def _find_tarifa(text: str) -> str | None:
    m = _TARIFA_RE.search(text)
    return m.group(1).upper() if m else None


def _clean_address(raw: str | None) -> str | None:
    if not raw:
        return None
    cleaned = re.sub(r"\s+\d{1,4}\s*$", "", raw.strip())
    return cleaned.strip(" ,;.")


def _find_consumos(text: str) -> tuple[str | None, str | None, str | None]:
    m = _CONSUMOS_RE.search(text)
    if m:
        return m.group(1), m.group(2), m.group(3)
    return (
        _first_group(_PUNTA_RE, text),
        _first_group(_LLANO_RE, text),
        _first_group(_VALLE_RE, text),
    )


def _find_total(text: str) -> float | None:
    m = _TOTAL_ELEC_RE.search(text)
    if m:
        return _to_float(m.group(1))
    m = _TOTAL_PAY_RE.search(text)
    if m:
        return _to_float(m.group(1))
    return None


def _find_period_days(text: str) -> int | None:
    for match in _PERIOD_RE.finditer(text):
        start = _parse_dotted_date(match.group(1))
        end = _parse_dotted_date(match.group(2))
        if start and end and end >= start:
            return (end - start).days + 1
    return None


def _parse_dotted_date(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%d.%m.%Y")
    except ValueError:
        return None


def _to_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _fill_defaults(record: dict[str, Any]) -> list[str]:
    defaulted: list[str] = []

    if "comercializadora_actual" not in record:
        record["comercializadora_actual"] = "DESCONOCIDA"
        defaulted.append("comercializadora_actual")
    if "cups" not in record:
        record["cups"] = "ES0000000000000000XX0"
        defaulted.append("cups")
    if "codigo_postal" not in record:
        record["codigo_postal"] = "08001"
        defaulted.append("codigo_postal")
    if "region" not in record:
        record["region"] = "barcelona"
        defaulted.append("region")
    if "tarifa_acceso" not in record:
        record["tarifa_acceso"] = "2.0TD"
        defaulted.append("tarifa_acceso")
    if "potencia_p1_kw" not in record:
        record["potencia_p1_kw"] = 4.6
        defaulted.append("potencia_p1_kw")
    if "periodo_facturacion_dias" not in record:
        record["periodo_facturacion_dias"] = 30
        defaulted.append("periodo_facturacion_dias")
    if "total_factura_eur" not in record:
        record["total_factura_eur"] = 75.0
        defaulted.append("total_factura_eur")

    total = record["total_factura_eur"]
    estimated_kwh = total / 0.21
    if "consumo_kwh_punta" not in record:
        record["consumo_kwh_punta"] = round(estimated_kwh * 0.30, 2)
        defaulted.append("consumo_kwh_punta")
    if "consumo_kwh_llano" not in record:
        record["consumo_kwh_llano"] = round(estimated_kwh * 0.45, 2)
        defaulted.append("consumo_kwh_llano")
    if "consumo_kwh_valle" not in record:
        record["consumo_kwh_valle"] = round(estimated_kwh * 0.25, 2)
        defaulted.append("consumo_kwh_valle")

    return defaulted
