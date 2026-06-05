# Motivs Factura

`factura.motivs.ai` — Spain electricity contract intelligence.

A user uploads their electricity bill (PDF). The service masks PII at the
ingest gate, extracts a structured consumption profile, and returns a
deterministically ranked top-10 of alternative public-market offers filtered
by region (Catalunya in v1).

The service is also a dogfood case for `motivs-sre`: two ingest paths, two
contracts, one deterministic match. PII never leaves the encrypted ephemeral
boundary.

## Stack

- Python 3.11+, FastAPI, Uvicorn
- `motivs-sre` SyncPipeline for the SRE gate
- LanceDB for the public offers index
- Redis for the short-lived masked user profile
- pdfplumber + Tesseract for bill OCR
- TanStack Start for the frontend (separate package, later)

## Run

```bash
python -m pip install -e .
cp .env.example .env
uvicorn backend.app.main:app --reload --port 8765
```

Health: `GET http://localhost:8765/healthz`.

## Layout

```
backend/
  app/          fastapi application
    core/       settings, logging
    motivs/     sre gate factory, emitter, per-upload wrapper
    api/routes/ http endpoints
  contracts/    motivs delivery contracts (yaml)
  tests/        pytest
```

## License

Proprietary, all rights reserved.
