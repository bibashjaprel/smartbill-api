#!/usr/bin/env python3
"""
Production Server Startup Script for BillSmart API
"""

import uvicorn
import os
from pathlib import Path


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

def main():
    """Start the FastAPI server"""
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)
    
    # Server configuration
    reload_enabled = _as_bool(os.getenv("RELOAD"), default=False)
    port = int(os.getenv("PORT", "8000"))

    config = {
        "app": "app.main:app",
        "host": "0.0.0.0",
        "port": port,
        "reload": reload_enabled,
        "log_level": "info",
        "access_log": True
    }
    
    print("🚀 Starting BillSmart API Server...")
    print(f"📡 Server will be available at: http://{config['host']}:{config['port']}")
    print(f"📖 API Documentation: http://{config['host']}:{config['port']}/docs")
    print(f"🔗 Alternative docs: http://{config['host']}:{config['port']}/redoc")
    
    # Start the server
    uvicorn.run(**config)

if __name__ == "__main__":
    main()
