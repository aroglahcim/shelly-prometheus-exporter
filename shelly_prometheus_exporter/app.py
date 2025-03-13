from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse
import httpx
import logging
from typing import List
import asyncio
from shelly_prometheus_exporter.metrics import fetch_device_metrics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Shelly Prometheus Exporter",
    description="A Prometheus exporter for Shelly devices",
    version="0.1.0"
)

def normalize_target_url(target: str) -> str:
    """Normalize the target URL to ensure it has a scheme."""
    if not target.startswith(('http://', 'https://')):
        return f'http://{target}'
    return target

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/metrics", response_class=PlainTextResponse)
async def get_metrics(target: List[str] = Query(None, alias="target[]")):
    """
    Get metrics from one or more Shelly devices.
    
    Args:
        target: List of URLs or IP addresses of Shelly devices
    
    Returns:
        Metrics from all devices in Prometheus format
    """
    if not target:
        raise HTTPException(status_code=400, detail="No targets specified")
    
    logger.info(f"Fetching metrics from targets: {target}")
    
    # Normalize all target URLs
    target_urls = [normalize_target_url(t) for t in target]
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Fetch metrics from all targets concurrently
            tasks = [fetch_device_metrics(client, url) for url in target_urls]
            results = await asyncio.gather(*tasks)
            
            # Combine all metrics
            return "\n".join(results)
            
    except Exception as e:
        logger.exception("Unexpected error while fetching metrics")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    ) 