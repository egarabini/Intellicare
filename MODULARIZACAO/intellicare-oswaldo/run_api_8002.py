#!/usr/bin/env python3
"""
Run Oswaldo API on port 8002.

Usage:
    python run_api_8002.py
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    PORT = int(os.getenv("OSWALDO_PORT", "8002"))
    HOST = os.getenv("OSWALDO_HOST", "0.0.0.0")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    print(f"""
    ╔════════════════════════════════════════╗
    ║  OSWALDO - Doenças Crônicas            ║
    ║  Iniciando em {HOST}:{PORT}             ║
    ║  Ambiente: {ENVIRONMENT:15} ║
    ║  Docs: http://localhost:{PORT}/api/docs ║
    ╚════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "src.oswaldo.api.main:app",
        host=HOST,
        port=PORT,
        reload=(ENVIRONMENT == "development")
    )
