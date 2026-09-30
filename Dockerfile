# Refresh this digest deliberately and validate with CI.
FROM python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN groupadd --system appgroup \
    && useradd --system --gid appgroup --home-dir /app appuser \
    && mkdir /data \
    && chown appuser:appgroup /data

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --require-hashes --only-binary=:all: -r requirements.txt \
    && pip check

COPY --chown=appuser:appgroup app ./app

ENV DATABASE_PATH=/data/ideas.db

EXPOSE 8080

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8080/health', timeout=3)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
