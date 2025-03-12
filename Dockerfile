# Build stage
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.7.1
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Configure Poetry
RUN poetry config virtualenvs.in-project true

# Copy Poetry configuration
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --only main --no-root

# Copy the rest of the application
COPY ./shelly_prometheus_exporter ./shelly_prometheus_exporter

# Install the package
RUN poetry install --only main

# Runtime stage
FROM python:3.12-slim

# Create non-root user
RUN useradd -m -u 1000 shelly

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy the application
COPY --from=builder /app/shelly_prometheus_exporter /app/shelly_prometheus_exporter

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Switch to non-root user
USER shelly

# Set working directory
WORKDIR /app

# Expose the port the app runs on
EXPOSE ${PORT}

# Command to run the application using the __main__.py entry point
CMD ["python", "-m", "shelly_prometheus_exporter"] 
