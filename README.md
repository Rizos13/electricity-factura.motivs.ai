# Motivs Electricity Factura

Compare your Spanish electricity bill against the public CNMC catalog. Runs locally on your Mac. Your bills never leave your device.

## Why local

Most comparators want you to upload your bill to their server, then ask you to trust them with that data. This one does the opposite:

- The whole pipeline runs on your Mac.
- The Motivs SRE security gate masks every PII field (CUPS, NIF, IBAN, address, name) before anything else happens, locally, in memory.
- After the comparison, the masked profile is dropped. No accounts, no logs sent anywhere.
- The only network traffic during a comparison is reading the bundled CNMC offer catalog from local disk.

If you don't trust us — install it, watch the network with Little Snitch, and verify.

## Install (macOS)

Requirements: Python 3.11 / 3.12 / 3.13, git.

```bash
curl -fsSL https://raw.githubusercontent.com/Rizos13/electricity-factura.motivs.ai/main/install.sh | bash
```

The installer:

1. Clones the latest source into `~/.motivs/factura/`
2. Creates an isolated Python virtual environment in that directory
3. Downloads the Motivs SRE security gate (bytecode-only wheel)
4. Installs all dependencies
5. Generates a per-install HMAC key (your masking secret, unique to your Mac)
6. Registers the `motivs-factura` command in `~/.local/bin`

Optional, for OCR on photographed bills (.jpg/.png):

```bash
brew install tesseract tesseract-lang
```

PDF bills work without Tesseract.

## Use

Start the service:

```bash
motivs-factura
```

It opens `http://127.0.0.1:8765` in your default browser. Drop a PDF or photo of your bill into the upload box.

Other commands:

```bash
motivs-factura status     # is it running?
motivs-factura stop       # stop the server
motivs-factura logs       # tail the local log
motivs-factura update     # pull latest source + refresh SRE gate
```

## What's open and what isn't

| Part | Source available |
|---|---|
| Frontend (HTML/CSS/JS) | Open, this repository |
| Backend (FastAPI app, extractor, tariff model, ranker) | Open, this repository |
| CNMC parser and bundled snapshot | Open, this repository |
| `motivs-sre` security gate | Proprietary, distributed as compiled wheel only |

The reasoning: the gate is the part you'd want to trust on your bill data. We ship it as a binary so you can verify behavior (network, file access, output) but don't expose the implementation to copy-paste cloning.

## Architecture

```
backend/
  app/
    core/       settings, logging
    motivs/     sre gate factory, emitter, per-upload wrapper
    factura/    pdf bill text extraction
    tariff/     2.0TD 2026 tariff model, bill decomposer, offer cost estimator
    cnmc/       CNMC pdf snapshot parser
    offers/     LanceDB offer index loader
    ranker/     deterministic offer ranking
    api/routes/ http endpoints (upload, result, bug-report)
  contracts/    motivs delivery contracts (yaml)
  tests/        pytest
frontend/       static html/css/js served by FastAPI
scripts/        launcher and ops scripts
install.sh      one-shot macOS installer
```

## Uninstall

```bash
motivs-factura stop
rm -rf ~/.motivs/factura ~/.local/bin/motivs-factura
```

## License

Frontend and backend source: see repository LICENSE (forthcoming).
Motivs SRE library: proprietary, see the LICENSE file shipped with the wheel.
