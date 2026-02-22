#!/usr/bin/env python
"""Simple script to start Geralda API on port 8006"""

import os
import sys
import uvicorn

# Change to project root if needed, but adding src to path is key
# We assume running from intellicare-geralda root
sys.path.insert(0, 'src')

if __name__ == "__main__":
    # Import here to verify it works
    try:
        from geralda.api.app import app
        print("[OK] Geralda App imported successfully. Starting Server on 8006...")
        uvicorn.run(app, host="0.0.0.0", port=8006, log_level="info")
    except Exception as e:
        print(f"[ERROR] Error importing Geralda App: {e}")
        sys.exit(1)
