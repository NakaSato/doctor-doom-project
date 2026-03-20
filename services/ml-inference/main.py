# Root main.py - Entry point wrapper
# This file allows running the service with: python main.py
# The actual application is in src/main.py

import uvicorn
from src.utils import get_settings

settings = get_settings()

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        workers=settings.workers,
    )
