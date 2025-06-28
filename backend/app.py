from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import bcrypt
import pyotp
import qrcode
import io
import base64
import os
import secrets
from datetime import datetime, timedelta
import jwt
from functools import wraps
import requests

app = Flask(__name__)
CORS(app)

# Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
ADMIN_KEY = os.environ.get('ADMIN_KEY', 'rAwwIzAd-RGz8eYGo_6ymz8Wd4EFEnBC6R--MWQ8gK8')
DATABASE = 'users.db'

app.config['SECRET_KEY'] = SECRET_KEY

def init_db():
    """Initialize the database with users table"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            hwid TEXT,
            totp_secret TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            discord_id TEXT,
            note TEXT
        )
    ''')
    
    # Ensure new columns exist when upgrading from older schema
    cursor.execute("PRAGMA table_info(users)")
    existing_cols = [row[1] for row in cursor.fetchall()]
    
    if 'expires_at' not in existing_cols:
        cursor.execute('ALTER TABLE users ADD COLUMN expires_at TIMESTAMP')
    if 'discord_id' not in existing_cols:
        cursor.execute('ALTER TABLE users ADD COLUMN discord_id TEXT')
    if 'note' not in existing_cols:
        cursor.execute('ALTER TABLE users ADD COLUMN note TEXT')
    
    conn.commit()
    conn.close()

def require_admin(f):
    """Decorator to require admin key for certain endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_key = request.headers.get('X-Admin-Key')
        if not admin_key or admin_key != ADMIN_KEY:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def generate_totp_qr(email, secret):
    """Generate QR code for TOTP setup"""
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name="Silica Client"
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for easy transmission
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return img_base64

@app.route('/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({'error': 'Email is required'}), 400
        
        email = data['email'].lower().strip()
        discord_id = data.get('discord_id')
        discord_username = data.get('discord_username')
        is_active = data.get('is_active', False)
        duration_days = data.get('duration_days', 0)
        
        # Generate random password
        password = secrets.token_urlsafe(12)
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        # Generate TOTP secret
        totp_secret = pyotp.random_base32()
        totp = pyotp.TOTP(totp_secret)
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp.provisioning_uri(email, issuer_name="Silica Client"))
        qr.make(fit=True)
        
        # Create QR code image
        img_buffer = io.BytesIO()
        qr.make_image(fill_color="black", back_color="white").save(img_buffer, format='PNG')
        qr_code = f"data:image/png;base64,{base64.b64encode(img_buffer.getvalue()).decode()}"
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Email already registered'}), 400
        
        # Calculate expiration if duration is provided
        expires_at = None
        if is_active and duration_days > 0:
            expires_at = datetime.now() + timedelta(days=duration_days)
        
        # Insert new user
        cursor.execute('''
            INSERT INTO users (email, password_hash, totp_secret, is_active, discord_id, expires_at, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (email, password_hash, totp_secret, is_active, discord_id, expires_at, discord_username))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'password': password,
            'totp_secret': totp_secret,
            'qr_code': qr_code
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@app.route('/auth/activate', methods=['POST'])
@require_admin
def activate_user():
    """Activate a user and set their duration (admin only)"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'duration_days' not in data:
            return jsonify({'error': 'Email and duration_days are required'}), 400
        
        email = data['email'].lower().strip()
        duration_days = int(data['duration_days'])
        
        if duration_days <= 0:
            return jsonify({'error': 'Duration must be positive'}), 400
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        # Calculate expiration date
        expires_at = datetime.now() + timedelta(days=duration_days)
        
        # Activate user and set duration
        cursor.execute('''
            UPDATE users 
            SET is_active = 1, expires_at = ?
            WHERE email = ?
        ''', (expires_at, email))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Failed to activate user'}), 500
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'User {email} activated successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Activation failed: {str(e)}'}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    """Login a user"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'password' not in data or 'totp' not in data:
            return jsonify({'error': 'Email, password and TOTP code are required'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        totp_code = data['totp']
        hwid = data.get('hwid')
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get user data
        cursor.execute('''
            SELECT id, password_hash, totp_secret, hwid, is_active, expires_at
            FROM users 
            WHERE email = ?
        ''', (email,))
        
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({'error': 'Invalid credentials'}), 401
        
        user_id, stored_hash, totp_secret, stored_hwid, is_active, expires_at = user
        
        # Check if user is active
        if not is_active:
            conn.close()
            return jsonify({'error': 'Account not activated. Please wait for admin approval.'}), 403
        
        # Check if account has expired
        if expires_at and datetime.now() > datetime.fromisoformat(expires_at):
            conn.close()
            return jsonify({'error': 'Account has expired. Please contact an admin.'}), 403
        
        # Verify password
        if not bcrypt.checkpw(password.encode(), stored_hash):
            conn.close()
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify TOTP
        totp = pyotp.TOTP(totp_secret)
        if not totp.verify(totp_code):
            conn.close()
            return jsonify({'error': 'Invalid 2FA code'}), 401
        
        # Check HWID
        if stored_hwid is None:
            # First login - store HWID
            cursor.execute('UPDATE users SET hwid = ?, last_login = ? WHERE id = ?',
                         (hwid, datetime.now(), user_id))
        elif stored_hwid != hwid:
            conn.close()
            return jsonify({'error': 'Hardware ID mismatch. Contact admin to reset.'}), 403
        else:
            # Update last login
            cursor.execute('UPDATE users SET last_login = ? WHERE id = ?',
                         (datetime.now(), user_id))
        
        conn.commit()
        conn.close()
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user_id,
            'email': email,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, SECRET_KEY, algorithm='HS256')
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': token
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@app.route('/auth/reset-hwid', methods=['POST'])
@require_admin
def reset_hwid():
    """Reset user's HWID (admin only)"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({'error': 'Email is required'}), 400
        
        email = data['email'].lower().strip()
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Update user's HWID to null
        cursor.execute('UPDATE users SET hwid = NULL WHERE email = ?', (email,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'HWID reset for {email}'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'HWID reset failed: {str(e)}'}), 500

@app.route('/auth/users', methods=['GET'])
@require_admin
def list_users():
    """List all users (admin only)"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT email, created_at, last_login, is_active, 
                   CASE WHEN hwid IS NOT NULL THEN 'Set' ELSE 'Not Set' END as hwid_status,
                   expires_at
            FROM users
            ORDER BY created_at DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'email': row[0],
                'created_at': row[1],
                'last_login': row[2],
                'is_active': bool(row[3]),
                'hwid_status': row[4],
                'expires_at': row[5]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'users': users
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to list users: {str(e)}'}), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'service': 'Silica Client Authentication Server',
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
    print("🏥 Health check endpoint accessed")
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
            'service': 'Silica Auth Server',
            'version': '1.0.0'
    }), 200
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/auth/check-discord', methods=['GET'])
def check_discord():
    """Check if a Discord user already has an account"""
    try:
        discord_id = request.args.get('discord_id')
        
        if not discord_id:
            return jsonify({'error': 'Discord ID is required'}), 400
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE discord_id = ?', (discord_id,))
        user = cursor.fetchone()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'has_account': user is not None
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Check failed: {str(e)}'}), 500

@app.route('/auth/add-duration', methods=['POST'])
@require_admin
def add_duration():
    """Add duration to a user's subscription"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'days' not in data:
            return jsonify({'error': 'Email and days are required'}), 400
        
        email = data['email'].lower().strip()
        days = int(data['days'])
        
        if days <= 0:
            return jsonify({'error': 'Days must be positive'}), 400
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get current expiry
        cursor.execute('SELECT expires_at, discord_id FROM users WHERE email = ?', (email,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        current_expiry, discord_id = result
        
        # Calculate new expiry
        if current_expiry:
            new_expiry = datetime.fromisoformat(current_expiry) + timedelta(days=days)
        else:
            new_expiry = datetime.now() + timedelta(days=days)
        
        # Update expiry
        cursor.execute('''
            UPDATE users 
            SET expires_at = ?
            WHERE email = ?
        ''', (new_expiry.isoformat(), email))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Added {days} days to {email}',
            'new_expiry': new_expiry.isoformat(),
            'discord_id': discord_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to add duration: {str(e)}'}), 500

@app.route('/auth/remove-duration', methods=['POST'])
@require_admin
def remove_duration():
    """Remove duration from a user's subscription"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'days' not in data:
            return jsonify({'error': 'Email and days are required'}), 400
        
        email = data['email'].lower().strip()
        days = int(data['days'])
        
        if days <= 0:
            return jsonify({'error': 'Days must be positive'}), 400
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get current expiry
        cursor.execute('SELECT expires_at, discord_id FROM users WHERE email = ?', (email,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        current_expiry, discord_id = result
        if not current_expiry:
            conn.close()
            return jsonify({'error': 'User has no expiry date set'}), 400
        
        # Calculate new expiry
        new_expiry = datetime.fromisoformat(current_expiry) - timedelta(days=days)
        if new_expiry < datetime.now():
            new_expiry = datetime.now()
        
        # Update expiry
        cursor.execute('''
            UPDATE users 
            SET expires_at = ?
            WHERE email = ?
        ''', (new_expiry.isoformat(), email))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Removed {days} days from {email}',
            'new_expiry': new_expiry.isoformat(),
            'discord_id': discord_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to remove duration: {str(e)}'}), 500

@app.route('/auth/reset-account', methods=['POST'])
@require_admin
def reset_account():
    """Reset a user's account"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({'error': 'Email is required'}), 400
        
        email = data['email'].lower().strip()
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get Discord ID before deleting
        cursor.execute('SELECT discord_id FROM users WHERE email = ?', (email,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        discord_id = result[0]
        
        # Delete user
        cursor.execute('DELETE FROM users WHERE email = ?', (email,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Reset account for {email}',
            'discord_id': discord_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to reset account: {str(e)}'}), 500

@app.route('/auth/user-info', methods=['GET'])
@require_admin
def get_user_info():
    """Get detailed user information"""
    try:
        email = request.args.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT email, discord_id, is_active, expires_at, last_login, 
                   created_at, hwid, note
            FROM users 
            WHERE email = ?
        ''', (email,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        user = {
            'email': result[0],
            'discord_id': result[1],
            'is_active': bool(result[2]),
            'expires_at': result[3],
            'last_login': result[4],
            'created_at': result[5],
            'hwid': result[6],
            'note': result[7]
        }
        
        conn.close()
        
        return jsonify({
            'success': True,
            'user': user
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get user info: {str(e)}'}), 500

@app.route('/auth/set-note', methods=['POST'])
@require_admin
def set_note():
    """Set an admin note for a user"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'note' not in data:
            return jsonify({'error': 'Email and note are required'}), 400
        
        email = data['email'].lower().strip()
        note = data['note']
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET note = ?
            WHERE email = ?
        ''', (note, email))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Updated note for {email}'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to set note: {str(e)}'}), 500

@app.route('/auth/reset-all-users', methods=['POST'])
@require_admin
def reset_all_users():
    """Reset all users (admin only)"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Reset all users
        cursor.execute('''
            UPDATE users 
            SET hwid = NULL,
                is_active = 0,
                expires_at = NULL,
                last_login = NULL
        ''')
        
        affected_rows = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Successfully reset {affected_rows} users',
            'affected_users': affected_rows
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to reset users: {str(e)}'}), 500

@app.route('/auth/validate', methods=['POST'])
def validate_token():
    """Validate a JWT token and HWID"""
    try:
        data = request.get_json()
        
        if not data or 'token' not in data or 'hwid' not in data:
            return jsonify({'error': 'Token and HWID are required'}), 400
        
        token = data['token']
        hwid = data['hwid']
        
        # Decode JWT token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_email = payload['email']
            user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get user data
        cursor.execute('''
            SELECT hwid, is_active, expires_at
            FROM users 
            WHERE id = ? AND email = ?
        ''', (user_id, user_email))
        
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        stored_hwid, is_active, expires_at = user
        
        # Check if user is active
        if not is_active:
            conn.close()
            return jsonify({'error': 'Account not activated'}), 403
        
        # Check if account has expired
        if expires_at and datetime.now() > datetime.fromisoformat(expires_at):
            conn.close()
            return jsonify({'error': 'Account has expired'}), 403
        
        # Check HWID
        if stored_hwid != hwid:
            conn.close()
            return jsonify({'error': 'Hardware ID mismatch'}), 403
        
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Token valid',
            'user': user_email
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500



@app.route('/auth/trigger-discord-register', methods=['POST'])
def trigger_discord_register():
    """Simulate a Discord !register command from website purchase"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'discord_username' not in data:
            return jsonify({'error': 'Email and discord_username are required'}), 400
        
        email = data['email'].lower().strip()
        discord_username = data['discord_username']
        product_type = data.get('product_type', 'monthly')
        payment_method = data.get('payment_method', 'unknown')
        payment_proof = data.get('payment_proof', '')
        discount_info = data.get('discount_info')
        final_price = data.get('final_price')
        
        # Calculate duration based on product type
        duration_days = 30 if product_type == 'monthly' else 1000
        
        # Generate random password (same as Discord bot does)
        password = secrets.token_urlsafe(12)
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        # Generate TOTP secret (same as Discord bot does)
        totp_secret = pyotp.random_base32()
        totp = pyotp.TOTP(totp_secret)
        
        # Generate QR code (same as Discord bot does)
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp.provisioning_uri(email, issuer_name="Silica Client"))
        qr.make(fit=True)
        
        # Create QR code image
        img_buffer = io.BytesIO()
        qr.make_image(fill_color="black", back_color="white").save(img_buffer, format='PNG')
        qr_code = f"data:image/png;base64,{base64.b64encode(img_buffer.getvalue()).decode()}"
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create note with purchase info
        note_parts = [f"Discord: {discord_username}"]
        if payment_method:
            note_parts.append(f"Payment: {payment_method}")
        if payment_proof:
            note_parts.append(f"Proof: {payment_proof}")
        if discount_info:
            note_parts.append(f"Discount: {discount_info['code']} (${discount_info['savings']:.2f} off)")
        if final_price:
            note_parts.append(f"Price: ${final_price:.2f}")
        
        note = " | ".join(note_parts)
        
        # Insert new user with INACTIVE status (same as Discord !register)
        # Admin will need to activate after verifying payment
        cursor.execute('''
            INSERT INTO users (email, password_hash, totp_secret, is_active, discord_id, note)
            VALUES (?, ?, ?, 0, NULL, ?)
        ''', (email, password_hash, totp_secret, note))
        
        conn.commit()
        conn.close()
        
        # Call Discord bot webhook to send DM
        try:
            webhook_response = requests.post('http://localhost:3001/webhook/register', json={
                'discord_username': discord_username,
                'email': email,
                'password': password,
                'totp_secret': totp_secret,
                'qr_code': qr_code,
                'product_type': product_type
            }, timeout=10)
            
            if webhook_response.status_code == 200:
                return jsonify({
                    'success': True,
                    'message': 'Registration complete! Check your Discord DMs for login credentials.',
                    'status': 'dm_sent'
                }), 200
            else:
                return jsonify({
                    'success': True,
                    'message': 'Account created but could not send Discord DM. Contact admin for credentials.',
                    'status': 'dm_failed',
                    'discord_error': webhook_response.text
                }), 200
                
        except requests.exceptions.RequestException as webhook_error:
            return jsonify({
                'success': True,
                'message': 'Account created but Discord bot is offline. Contact admin for credentials.',
                'status': 'bot_offline',
                'webhook_error': str(webhook_error)
            }), 200
        
    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

# Initialize database when module is imported
print("🔧 Initializing database...")
try:
    init_db()
    print("✅ Database initialized successfully")
except Exception as e:
    print(f"❌ Database initialization failed: {str(e)}")
    raise

if __name__ == '__main__':
    # This is only for local development
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    print("🚀 Starting Silica Auth Backend (Development Mode)...")
    print(f"📡 Server running on: {host}:{port}")
    print(f"🔑 Admin Key: {ADMIN_KEY}")
    app.run(host=host, port=port, debug=True) 