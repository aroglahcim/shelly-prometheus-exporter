import uvicorn
from .settings import get_settings

def main():
    """Run the application using Uvicorn."""
    settings = get_settings()
    uvicorn.run(
        "shelly_prometheus_exporter.app:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEV_RELOAD
    )

if __name__ == "__main__":
    main()
