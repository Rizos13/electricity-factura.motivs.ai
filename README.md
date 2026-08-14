# Motivs Electricity Factura

Compare your Spanish electricity bill against the public CNMC catalog. Runs locally on your Mac. Your bills never leave your device.

## Why local

Most comparators want you to upload your bill to their server, then ask you to trust them with that data. This one does the opposite:

- The whole pipeline runs on your Mac.
- The Motivs Guard security gate masks every PII field (CUPS, NIF, IBAN, address, name) before anything else happens, locally, in memory.
- After the comparison, the masked profile is dropped. No accounts, no logs sent anywhere.
- The only network traffic during a comparison is reading the bundled CNMC offer catalog from local disk.

If you don't trust us — install it, watch the network with Little Snitch, and verify.

## Install (macOS)

Requirements: Python 3.13, git. If you don't have Python 3.13 yet: `brew install python@3.13`.

```bash
curl -fsSL https://raw.githubusercontent.com/Rizos13/electricity-factura.motivs.ai/main/install.sh | bash
```

The installer:

1. Clones the latest source into `~/.motivs/factura/`
2. Creates an isolated Python virtual environment in that directory
3. Downloads the Motivs Guard security gate, a compiled wheel, and verifies its checksum
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
motivs-factura update     # pull latest source + refresh the security gate
```

## What's open and what isn't

| Part | Source available |
|---|---|
| Frontend (HTML/CSS/JS) | Open, this repository |
| Backend (FastAPI app, extractor, tariff model, ranker) | Open, this repository |
| CNMC parser and bundled snapshot | Open, this repository |
| Motivs Guard security gate | Licensed product, shipped as a compiled wheel |

Everything specific to comparing electricity bills is in this repository and you can read all of it. The security gate is a separate commercial product that this app licenses, so its source is not published here. What you can verify is its behaviour: watch its network activity, its file access, and what it hands back. The wheel is published with a SHA256 checksum that this repository pins, so you can confirm you installed the same artifact we did.

## The security gate, and using it in your own product

Motivs Guard is the layer between untrusted incoming data and whatever consumes it downstream, an AI model, a warehouse, a billing system. In this app it is what reads your bill: it masks every PII field (CUPS, NIF, IBAN, address, name) in memory before any other code sees the document.

It is a Python library, not a service. You embed it in the backend you already run, and it works against a contract you write in YAML describing what the data is allowed to look like. Each file comes back with one of three verdicts:

| Verdict | Meaning |
|---|---|
| DELIVERED | the file matched the contract, transformations applied, safe to pass on |
| AWAITING_APPROVAL | the file changed in a plausible way, an operator decides before it moves |
| QUARANTINED | the file violated the contract, it is isolated with evidence and never reaches the consumer |

What it does on the way there: validates structure and values against your contract, scans content for injection attempts, tokenizes PII with HMAC so joins still work but the original cannot be recovered, and remembers operator decisions so an approved change is auto approved next time.

If you have a pipeline where untrusted files reach something expensive to get wrong, it is licensable for your project. Open an issue in this repository to start a conversation.

## Architecture

```
backend/
  app/
    core/       settings, logging
    motivs/     security gate factory, emitter, per-upload wrapper
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
Motivs Guard: proprietary, see the LICENSE file shipped with the wheel.
