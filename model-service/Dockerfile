# --- Build stage: install dependencies into a venv, keep build tools out of final image ---
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Runtime stage: slim image, no compilers, non-root user ---
FROM python:3.11-slim

RUN groupadd -r mediguard && useradd -r -g mediguard -d /app mediguard

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY app/ ./app/
COPY gunicorn_conf.py .

RUN chown -R mediguard:mediguard /app
USER mediguard

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health/live', timeout=3)" || exit 1

CMD ["gunicorn", "-c", "gunicorn_conf.py", "app.main:app"]
