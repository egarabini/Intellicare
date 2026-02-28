#!/usr/bin/env python
"""
Startup script for Oswaldo API on port 8002
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

if __name__ == "__main__":
    import uvicorn
    from src.oswaldo.api.main import app
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        reload=False
    )
