# -*- coding: utf-8 -*-
"""
AutoGeo Backend Entry Point
允许使用: python -m backend
"""

from backend.main import app

if __name__ == "__main__":
    import uvicorn
    from backend.config import HOST, PORT

    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
