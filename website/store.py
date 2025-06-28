from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import os
import secrets
import stripe
import sqlite3
from datetime import datetime, timedelta
import requests
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure CORS to allow requests from your domain
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://silicaclient.store",
            "http://localhost:3000",
            "http://localhost:5000"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-Admin-Key", "Authorization"]
    }
})

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_your_stripe_secret_key')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_your_webhook_secret')
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:5000')
ADMIN_KEY = os.environ.get('ADMIN_KEY', 'rAwwIzAd-RGz8eYGo_6ymz8Wd4EFEnBC6R--MWQ8gK8')
DATABASE = 'purchases.db'

stripe.api_key = STRIPE_SECRET_KEY

# Product configuration
PRODUCTS = {
    'lifetime': {
        'name': 'Silica Client - Lifetime License',
        'price': 2000,  # $20.00 in cents
        'duration_days': 1000,
        'stripe_price_id': os.environ.get('STRIPE_LIFETIME_PRICE_ID', 'price_lifetime')
    },
    'monthly': {
        'name': 'Silica Client - Monthly License',
        'price': 500,  # $5.00 in cents
        'duration_days': 30,
        'stripe_price_id': os.environ.get('STRIPE_MONTHLY_PRICE_ID', 'price_monthly')
    }
}

def init_db():
    """Initialize the purchases database"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id TEXT UNIQUE NOT NULL,
            discord_username TEXT NOT NULL,
            email TEXT NOT NULL,
            product_type TEXT NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            stripe_session_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Homepage with features and product information"""
    return render_template('index.html')

@app.route('/purchase')
def purchase():
    """Purchase page"""
    return render_template('purchase.html')

@app.route('/api/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Create a Stripe checkout session"""
    try:
        data = request.get_json()
        
        if not data or 'discord_username' not in data or 'email' not in data or 'product_type' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        discord_username = data['discord_username']
        email = data['email'].lower().strip()
        product_type = data['product_type']
        
        if product_type not in PRODUCTS:
            return jsonify({'error': 'Invalid product type'}), 400
        
        product = PRODUCTS[product_type]
        purchase_id = str(uuid.uuid4())
        
        # Store purchase in database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO purchases (purchase_id, discord_username, email, product_type, amount, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        ''', (purchase_id, discord_username, email, product_type, product['price']))
        
        conn.commit()
        conn.close()
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product['name'],
                        'description': f'Access to Silica Client for {product["duration_days"]} days'
                    },
                    'unit_amount': product['price'],
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('cancel', _external=True),
            metadata={
                'purchase_id': purchase_id,
                'discord_username': discord_username,
                'email': email,
                'product_type': product_type
            }
        )
        
        # Update purchase with Stripe session ID
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE purchases SET stripe_session_id = ? WHERE purchase_id = ?
        ''', (checkout_session.id, purchase_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'checkout_url': checkout_session.url}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to create checkout session: {str(e)}'}), 500

@app.route('/api/stripe-webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400
    
    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Retrieve metadata
        purchase_id = session['metadata']['purchase_id']
        discord_username = session['metadata']['discord_username']
        email = session['metadata']['email']
        product_type = session['metadata']['product_type']
        
        # Update purchase status
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE purchases 
            SET status = 'completed', completed_at = ?
            WHERE purchase_id = ?
        ''', (datetime.now(), purchase_id))
        
        conn.commit()
        conn.close()
        
        # Register and activate the user through the backend API
        try:
            # Create account and activate it
            duration_days = PRODUCTS[product_type]['duration_days']
            
            purchase_response = requests.post(f'{BACKEND_URL}/auth/purchase-complete', 
                json={
                    'email': email,
                    'discord_username': discord_username,
                    'duration_days': duration_days
                }
            )
            
            if purchase_response.status_code == 200:
                # Send notification to Discord webhook (optional)
                # This can notify your Discord server about new purchases
                pass
                    
        except Exception as e:
            print(f"Error processing purchase completion: {str(e)}")
    
    return 'Success', 200

@app.route('/success')
def success():
    """Success page after payment"""
    return render_template('success.html')

@app.route('/cancel')
def cancel():
    """Cancel page if payment is cancelled"""
    return render_template('cancel.html')

@app.route('/api/check-purchase/<purchase_id>')
def check_purchase(purchase_id):
    """Check purchase status"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT status, discord_username, email, product_type
        FROM purchases
        WHERE purchase_id = ?
    ''', (purchase_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return jsonify({
            'status': result[0],
            'discord_username': result[1],
            'email': result[2],
            'product_type': result[3]
        }), 200
    else:
        return jsonify({'error': 'Purchase not found'}), 404

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8000, debug=True) 