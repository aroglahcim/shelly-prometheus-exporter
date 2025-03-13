FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=1.7.1
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

RUN poetry config virtualenvs.in-project true

COPY pyproject.toml poetry.lock* ./

RUN poetry install --only main --no-root

COPY ./shelly_prometheus_exporter ./shelly_prometheus_exporter

RUN poetry install --only main

FROM python:3.12-slim

RUN useradd -m -u 1000 shelly

COPY --from=builder /app/.venv /app/.venv

COPY --from=builder /app/shelly_prometheus_exporter /app/shelly_prometheus_exporter

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER shelly

WORKDIR /app

CMD ["python", "-m", "shelly_prometheus_exporter"] 
