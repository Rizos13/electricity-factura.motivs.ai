from __future__ import annotations

import argparse
import csv
import io
import json
import logging
from datetime import date
from pathlib import Path

from motivs_core import Verdict

from backend.app.cnmc.parser import parse_cnmc_pdf
from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging
from backend.app.motivs.factory import build_pipeline


CONTRACT_FIELDS = (
    "offer_id",
    "comercializadora",
    "oferta",
    "tipo_precio",
    "importe_primera_factura_eur",
    "descuento_promocional_eur",
    "validez_texto",
    "servicios_adicionales",
    "penalizacion",
    "verde",
    "snapshot_date",
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest a CNMC pdf snapshot through the ofertas motivs pipeline.",
    )
    parser.add_argument("snapshot", type=Path, help="Path to a CNMC ListadoOfertas pdf")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Where to write delivered offers jsonl. Defaults to settings.artifact_dir/offers.jsonl",
    )
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings)
    logger = logging.getLogger(__name__)

    output_path: Path = args.output or settings.artifact_dir / "offers.jsonl"

    pdf_bytes = args.snapshot.read_bytes()
    records = parse_cnmc_pdf(pdf_bytes)
    logger.info(
        "parsed_offers",
        extra={"count": len(records), "snapshot": str(args.snapshot)},
    )
    if not records:
        logger.error("no_offers_parsed")
        return 2

    records = _fill_missing_snapshot_date(records)
    csv_bytes = _records_to_csv(records)

    pipeline, _ = build_pipeline(settings, kind="ofertas", shadow_baseline_required=False)
    result = pipeline.run(file_bytes=csv_bytes, file_name=args.snapshot.name + ".csv")
    logger.info(
        "pipeline_result",
        extra={"verdict": result.verdict.value, "run_id": result.run_id},
    )

    if result.verdict == Verdict.DELIVERED:
        rows = result.output_rows or []
        _write_jsonl(output_path, rows)
        logger.info(
            "offers_written",
            extra={"path": str(output_path), "count": len(rows)},
        )
        return 0
    if result.verdict == Verdict.AWAITING_APPROVAL:
        logger.warning("awaiting_approval", extra={"run_id": result.run_id})
        return 3
    if result.verdict == Verdict.QUARANTINED:
        logger.error("quarantined", extra={"run_id": result.run_id})
        return 4
    return 5


def _fill_missing_snapshot_date(records: list[dict]) -> list[dict]:
    today_iso = date.today().isoformat()
    return [
        {**r, "snapshot_date": r.get("snapshot_date") or today_iso}
        for r in records
    ]


def _records_to_csv(records: list[dict]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(CONTRACT_FIELDS), quoting=csv.QUOTE_ALL)
    writer.writeheader()
    for record in records:
        writer.writerow({
            field: (record.get(field) if record.get(field) is not None else "")
            for field in CONTRACT_FIELDS
        })
    return buf.getvalue().encode("utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
