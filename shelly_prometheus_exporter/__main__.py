import uvicorn

def main():
    """Run the application using Uvicorn."""
    uvicorn.run(
        "shelly_prometheus_exporter.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Enable auto-reload during development
    )

if __name__ == "__main__":
    main()
