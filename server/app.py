"""
Server entry point for OpenEnv compatibility.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sql_arena.server import app
import uvicorn


def main():
    """Main entry point to run the server."""
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()