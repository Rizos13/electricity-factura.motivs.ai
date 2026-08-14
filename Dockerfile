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

ARG MOTIVS_SRE_WHEEL_URL="https://github.com/Rizos13/guard-dist/releases/download/v0.8.0/motivs_guard-0.8.0-cp313-none-any.whl"
# checksum kept here rather than fetched next to the artifact, so a replaced
# release does not also get to replace what it is checked against
ARG MOTIVS_SRE_WHEEL_SHA256="b7b2083beaeb47d2c398fa2df5b5b51ffd8917eeacd02da14211f09ebc394e2e"

# pip parses the wheel filename for metadata, so it has to keep its own name
RUN pip install --upgrade pip && \
    wheel_name="$(basename "$MOTIVS_SRE_WHEEL_URL")" && \
    curl -fsSL "$MOTIVS_SRE_WHEEL_URL" -o "/tmp/$wheel_name" && \
    echo "${MOTIVS_SRE_WHEEL_SHA256}  /tmp/$wheel_name" | sha256sum -c - && \
    pip install "/tmp/$wheel_name" && \
    rm -f "/tmp/$wheel_name" && \
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
