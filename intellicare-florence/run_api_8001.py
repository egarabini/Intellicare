#!/usr/bin/env python
"""Simple script to start Florence API on port 8001"""

import os
import sys

# Change to project root
os.chdir(r'C:\DOCSHARE\INTELLICARE\intellicare-florence')

# Add src to path
sys.path.insert(0, 'src')

# Import and run
from florence.api.main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
