#!/usr/bin/env python3
import uvicorn

from torale.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "torale.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
