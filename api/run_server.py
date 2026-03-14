#!/usr/bin/env python3
"""
FastAPI Server Startup Script

Simple script to start the SHOP-BY-INTENTION API server.
"""

import sys
import os
import uvicorn

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def main():
    """Start the FastAPI server."""
    print("🚀 Starting SHOP-BY-INTENTION API Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("🌐 Frontend interface: http://localhost:8000/")
    print("📋 API documentation: http://localhost:8000/docs")
    print("🔍 Interactive docs: http://localhost:8000/redoc")
    print()
    
    try:
        uvicorn.run(
            "api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()