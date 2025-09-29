"""
TechKey Analysis - Main Application Entry Point
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Initialize database first
try:
    from init_db import init_db, create_sample_data
    init_db()
    create_sample_data()
except Exception as e:
    print(f"Warning: Database initialization issue: {e}")

from web.app import create_app

if __name__ == '__main__':
    app = create_app()
    
    print("🚀 Starting TechKey Analysis Web Application...")
    print("📍 Dashboard: http://localhost:5000")
    print("🔑 Login: admin / admin123")
    print("📊 Database: instance/app.db")
    
    # Run without debug mode to prevent constant reloading
    app.run(debug=False, host='127.0.0.1', port=5000)