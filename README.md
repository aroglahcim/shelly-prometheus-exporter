## Docker compose run

```yaml
services:
  shelly-prometheus-exporter:
    image: aroglahcim/shelly-prometheus-exporter
    container_name: shelly-prometheus-exporter
    restart: unless-stopped
    ports:
        - ${SHELLY_PROMETHEUS_EXPORTER_PORT:-8000}:${SHELLY_PROMETHEUS_EXPORTER_PORT:-8000}
    environment:
        - SHELLY_PROMETHEUS_EXPORTER_PORT=${SHELLY_PROMETHEUS_EXPORTER_PORT:-8000}
    volumes:
        - ./shelly_prometheus_exporter/:/app/shelly_prometheus_exporter/
    healthcheck:
        test: ["CMD", "curl", "-f", "http://localhost:${SHELLY_PROMETHEUS_EXPORTER_PORT:-8000}/health"]
        interval: 30s
        timeout: 10s
        retries: 3
        start_period: 10s
```

## Prometheus configuration

```yaml
scrape_configs:
  - job_name: shelly
    scrape_interval: 30s
    metrics_path: "/metrics"
    params:
      target[]: [ "plug-1.local", "plug-2.local", "plug-3.local", "plug-4.local" ]  # List of target values
    static_configs:
      - targets: [ "shelly-prometheus-exporter.local:8000" ]  # The scraper host
```
