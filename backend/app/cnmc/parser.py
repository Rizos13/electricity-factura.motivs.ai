from __future__ import annotations

import hashlib
import io
import re
from datetime import date
from typing import Any

import pdfplumber


_EUR_RE = re.compile(r"([0-9]+(?:[.,][0-9]+)?)")
_DATE_RE = re.compile(r"Fecha generaci[oó]n:\s*(\d{1,2})/(\d{1,2})/(\d{4})")


def parse_cnmc_pdf(pdf_bytes: bytes) -> list[dict[str, Any]]:
    """Map a CNMC ListadoOfertas pdf to oferta records."""
    snapshot_date = _extract_snapshot_date(pdf_bytes)
    offers: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                if not table or len(table) < 2:
                    continue
                section = _detect_section(table[0])
                if section == "unknown":
                    continue
                for raw_row in table[1:]:
                    record = _row_to_oferta(raw_row, section, snapshot_date)
                    if record and record["offer_id"] not in seen_ids:
                        seen_ids.add(record["offer_id"])
                        offers.append(record)
    return offers


def _extract_snapshot_date(pdf_bytes: bytes) -> date | None:
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in reversed(pdf.pages):
            text = page.extract_text() or ""
            match = _DATE_RE.search(text)
            if match:
                day, month, year = (int(g) for g in match.groups())
                return date(year, month, day)
    return None


def _detect_section(header_row: list[str | None]) -> str:
    joined = " ".join(_clean(c or "") for c in header_row).lower()
    if "tipo" in joined and "tarifa" in joined:
        return "mercado_libre"
    if "importe facturado" in joined:
        return "pvpc"
    return "unknown"


def _row_to_oferta(
    raw_row: list[str | None],
    section: str,
    snapshot_date: date | None,
) -> dict[str, Any] | None:
    row = [_clean(c or "") for c in raw_row]
    if not any(row):
        return None

    if section == "mercado_libre" and len(row) >= 9:
        comercializadora, oferta, tipo, importe, descuento, validez, servicios, pen, verde = row[:9]
        tipo_precio = _map_tipo(tipo)
    elif section == "pvpc" and len(row) >= 7:
        comercializadora, oferta, importe, validez, servicios, pen, verde = row[:7]
        descuento = ""
        tipo_precio = "pvpc"
    else:
        return None

    if not comercializadora or not oferta:
        return None

    importe_eur = _euros(importe)
    if importe_eur is None:
        return None

    return {
        "offer_id": _offer_id(comercializadora, oferta, tipo_precio),
        "comercializadora": comercializadora,
        "oferta": oferta,
        "tipo_precio": tipo_precio,
        "importe_primera_factura_eur": importe_eur,
        "descuento_promocional_eur": _euros(descuento),
        "validez_texto": validez or None,
        "servicios_adicionales": servicios or None,
        "penalizacion": _yes_no(pen),
        "verde": _yes_no(verde),
        "snapshot_date": snapshot_date.isoformat() if snapshot_date else None,
    }


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _offer_id(*parts: str) -> str:
    return hashlib.sha256(" | ".join(parts).encode("utf-8")).hexdigest()[:16]


def _euros(text: str) -> float | None:
    if not text:
        return None
    match = _EUR_RE.search(text)
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


def _map_tipo(text: str) -> str:
    lowered = text.lower()
    if "flexible" in lowered or "indexa" in lowered:
        return "flexible"
    return "fijo"


def _yes_no(text: str) -> str:
    return "si" if text.strip().lower().startswith("s") else "no"
