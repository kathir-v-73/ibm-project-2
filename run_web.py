#!/usr/bin/env python3
"""
TechKey Analysis - Web Application Launcher
"""

import os
from web.app import create_app

app = create_app()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "True").lower() == "true"
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=debug,
        threaded=True
    )