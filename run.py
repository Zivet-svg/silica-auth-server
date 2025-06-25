#!/usr/bin/env python3
"""
Simple runner script for Railway deployment
This script runs the Flask app from the root directory
"""

import os
import sys

# Add the backend directory to Python path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

# Change working directory to backend
os.chdir(backend_dir)

# Import and run the Flask app
if __name__ == '__main__':
    from app import app
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    app.run(host=host, port=port, debug=False) 