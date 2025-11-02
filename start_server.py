#!/usr/bin/env python3
"""
Production Server Startup Script for BillSmart API
"""

import uvicorn
import os
from pathlib import Path

def main():
    """Start the FastAPI server"""
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)
    
    # Server configuration
    config = {
        "app": "app.main:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": True,  # Set to False in production
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
