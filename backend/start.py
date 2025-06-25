#!/usr/bin/env python3
"""
Silica Client Authentication Backend
Quick start script for development and production
"""

import os
import sys
import subprocess
import sqlite3
from datetime import datetime

def check_dependencies():
    """Check if all required packages are installed"""
    try:
        import flask
        import bcrypt
        import pyotp
        import qrcode
        import jwt
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True

def setup_environment():
    """Set up environment variables if not already set"""
    if not os.environ.get('SECRET_KEY'):
        import secrets
        os.environ['SECRET_KEY'] = secrets.token_hex(32)
        print("🔑 Generated SECRET_KEY")
    
    if not os.environ.get('ADMIN_KEY'):
        os.environ['ADMIN_KEY'] = 'rAwwIzAd-RGz8eYGo_6ymz8Wd4EFEnBC6R--MWQ8gK8'
        print("🔑 Using default ADMIN_KEY")
        print(f"📝 Admin Key: {os.environ['ADMIN_KEY']}")
        print("   ⚠️  This key is used for Discord bot configuration")

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Create users table with Discord tracking and admin notes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash BLOB NOT NULL,
        totp_secret TEXT NOT NULL,
        hwid TEXT,
        is_active INTEGER DEFAULT 0,
        expires_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_login TEXT,
        discord_id TEXT UNIQUE,
        note TEXT
    )
    ''')
    
    # Create admin table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        discord_role_id TEXT UNIQUE NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    print('Database initialized with Discord tracking and admin notes')

def main():
    print("🚀 Starting Silica Client Authentication Backend")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Import and start the app
    try:
        from app import app, init_db
        
        # Initialize database
        print("📊 Initializing database...")
        init_db()
        print("✅ Database initialized")
        
        # Start the server
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('DEBUG', 'False').lower() == 'true'
        
        print(f"🌐 Starting server on port {port}")
        print(f"🔧 Debug mode: {debug}")
        print("=" * 50)
        
        app.run(host='0.0.0.0', port=port, debug=debug)
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 