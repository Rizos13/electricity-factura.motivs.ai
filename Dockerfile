FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      curl \
      tesseract-ocr \
      tesseract-ocr-spa \
      tesseract-ocr-eng \
      libgl1 \
      libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install "https://github.com/Rizos13/sre-dist/releases/latest/download/motivs_sre-0.5.0-py3-none-any.whl" && \
    pip install \
      "fastapi>=0.115.0" \
      "uvicorn[standard]>=0.30.0" \
      "python-multipart>=0.0.9" \
      "pydantic-settings>=2.4.0" \
      "orjson>=3.10.0" \
      "pyyaml>=6.0" \
      "lancedb>=0.15.0" \
      "pyarrow>=15.0.0" \
      "pandas>=2.2.0" \
      "numpy>=1.26.0" \
      "redis>=5.0.0" \
      "httpx>=0.27.0" \
      "pdfplumber>=0.11.0" \
      "pymupdf>=1.24.0" \
      "pytesseract>=0.3.10" \
      "pillow>=10.4.0"

COPY backend ./backend
COPY frontend ./frontend
RUN pip install --no-deps -e .

EXPOSE 10000
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
