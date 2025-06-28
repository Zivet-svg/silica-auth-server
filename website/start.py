#!/usr/bin/env python3
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from store import app

if __name__ == '__main__':
    port = int(os.environ.get('STORE_PORT', 8000))
    host = os.environ.get('STORE_HOST', '0.0.0.0')
    
    print("🛍️  Starting Silica Client Store...")
    print(f"🌐 Store URL: http://{host}:{port}")
    print(f"💳 Stripe Integration: {'Configured' if os.environ.get('STRIPE_SECRET_KEY') else 'Not Configured'}")
    print("\n⚠️  Important: Make sure to configure Stripe keys in environment variables!")
    
    app.run(host=host, port=port, debug=False) 