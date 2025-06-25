# 🛡️ Silica Client Authentication Server

A secure authentication system for the Silica Minecraft client with Discord bot management.

## 🚀 Features

- **🔐 JWT Authentication** with 2FA (TOTP)
- **💻 Hardware ID Binding** (one license per PC)
- **📱 Discord Bot Management** for user registration and admin controls
- **⏰ Account Expiration** and duration management
- **🔑 Admin Controls** via Discord commands
- **🛡️ Rate Limiting** and security features

## 📋 Components

### Backend API (`/backend`)
- Flask-based REST API
- SQLite database for user management
- JWT token authentication
- HWID verification system

### Discord Bot (`/discord-bot`)
- User registration and activation
- Admin management commands
- Account duration control
- User information and statistics

## 🔧 Setup

### 1. Clone Repository
```bash
git clone https://github.com/your-username/silica-auth-server.git
cd silica-auth-server
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### 3. Discord Bot Setup
```bash
cd discord-bot
npm install
npm start
```

### 4. Environment Configuration
Create `.env` files in both directories:

**backend/.env:**
```env
SECRET_KEY=your_secret_key_here
ADMIN_KEY=rAwwIzAd-RGz8eYGo_6ymz8Wd4EFEnBC6R--MWQ8gK8
PORT=5000
```

**discord-bot/.env:**
```env
DISCORD_TOKEN=your_bot_token_here
BACKEND_URL=http://localhost:5000
ADMIN_KEY=rAwwIzAd-RGz8eYGo_6ymz8Wd4EFEnBC6R--MWQ8gK8
AUTHORIZED_SERVER_ID=your_discord_server_id
```

## 🌐 Cloud Deployment

### Railway (Recommended)
1. Connect this repository to Railway
2. Deploy backend and bot as separate services
3. Set environment variables in Railway dashboard

### Heroku
1. Create two Heroku apps (backend + bot)
2. Set buildpacks and environment variables
3. Deploy via Git push

### Manual VPS
1. Clone repository on your server
2. Set up PM2 or systemd services
3. Configure reverse proxy (nginx)

## 📚 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login with HWID
- `POST /auth/validate` - Validate JWT token
- `POST /auth/reset-hwid` - Reset user HWID (admin)

### Admin Management
- `GET /auth/users` - List all users (admin)
- `POST /auth/activate` - Activate user account (admin)
- `POST /auth/add-duration` - Add subscription time (admin)
- `POST /auth/remove-duration` - Remove subscription time (admin)

## 🤖 Discord Commands

### User Commands
- `!register <email>` - Register new account
- `!help` - Show available commands

### Admin Commands
- `!activate <email> <days>` - Activate user for X days
- `!reset-hwid <email>` - Reset user's hardware ID
- `!add-duration <email> <days>` - Add subscription time
- `!remove-duration <email> <days>` - Remove subscription time
- `!user-info <email>` - Get user information
- `!list-users` - List all registered users
- `!reset-all-users` - Reset all user accounts

## 🔒 Security Features

- **HWID Binding**: Each account locked to specific hardware
- **2FA Required**: TOTP authentication mandatory
- **JWT Tokens**: Secure session management with expiration
- **Rate Limiting**: Prevents brute force attacks
- **Admin Authentication**: All admin actions require verification
- **Account Expiration**: Time-based access control

## 📊 Database Schema

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    hwid TEXT,
    totp_secret TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);
```

## 🛠️ Development

### Running Locally
```bash
# Terminal 1 - Backend
cd backend
python app.py

# Terminal 2 - Discord Bot  
cd discord-bot
npm run dev
```

### Environment Variables
All sensitive configuration should be in `.env` files (never commit these!)

### Contributing
1. Fork the repository
2. Create feature branch
3. Make changes and test
4. Submit pull request

## 📝 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues or questions:
1. Check existing GitHub issues
2. Create new issue with detailed description
3. Include logs and error messages

---

**⚠️ Security Note**: Always use HTTPS in production and keep your environment variables secure! 