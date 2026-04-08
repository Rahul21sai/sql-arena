"""
Server entry point for OpenEnv compatibility.
This file re-exports the FastAPI app from the main server module.
"""

import sys
import os

# Add parent directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sql_arena.server import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)