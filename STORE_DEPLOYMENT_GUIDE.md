# Silica Client Store Deployment Guide

This guide will help you deploy the complete Silica Client store with payment processing on your Ubuntu server.

## Prerequisites

- Ubuntu 20.04 or later
- Python 3.8+
- Domain name (recommended)
- Stripe account for payment processing

## Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install python3-pip python3-venv nginx certbot python3-certbot-nginx screen -y
```

## Step 2: Clone and Setup Project

```bash
# Clone the repository
cd /home/ubuntu
git clone [your-repo-url] silica-client
cd silica-client/silica-auth-server

# Create virtual environments
python3 -m venv backend/venv
python3 -m venv website/venv
```

## Step 3: Setup Backend Authentication Server

```bash
# Activate backend virtual environment
source backend/venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Create .env file
cat > .env << EOL
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
ADMIN_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
HOST=0.0.0.0
PORT=5000
EOL

# Test the backend
python app.py

# Exit with Ctrl+C when confirmed working
deactivate
cd ..
```

## Step 4: Setup Store Website

```bash
# Activate website virtual environment
source website/venv/bin/activate

# Install dependencies
cd website
pip install -r requirements.txt

# Create .env file (replace with your actual Stripe keys)
cat > .env << EOL
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
BACKEND_URL=http://localhost:5000
ADMIN_KEY=YOUR_ADMIN_KEY_FROM_BACKEND
STORE_HOST=0.0.0.0
STORE_PORT=8000
EOL

# Test the store
python store.py

# Exit with Ctrl+C when confirmed working
deactivate
cd ..
```

## Step 5: Setup Discord Bot

```bash
# Navigate to Discord bot directory
cd discord-bot

# Install Node.js if not already installed
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Install dependencies
npm install

# Create .env file (replace with your actual values)
cat > .env << EOL
DISCORD_TOKEN=your_discord_bot_token
BACKEND_URL=http://localhost:5000
ADMIN_KEY=YOUR_ADMIN_KEY_FROM_BACKEND
ADMIN_ROLE_ID=your_admin_role_id
ALLOWED_ROLE_ID=your_allowed_role_id
ALLOWED_CHANNELS=channel_id_1,channel_id_2
AUTHORIZED_SERVER_ID=your_server_id
EOL

cd ..
```

## Step 6: Configure Nginx

```bash
# Create Nginx configuration for the store
sudo nano /etc/nginx/sites-available/silica-store

# Add the following configuration:
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/stripe-webhook {
        proxy_pass http://localhost:8000/api/stripe-webhook;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Important for Stripe webhooks
        proxy_buffering off;
        proxy_request_buffering off;
    }
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/silica-store /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Setup SSL (replace with your domain)
sudo certbot --nginx -d your-domain.com
```

## Step 7: Create Systemd Services

### Backend Service
```bash
sudo nano /etc/systemd/system/silica-backend.service
```

```ini
[Unit]
Description=Silica Auth Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/silica-client/silica-auth-server/backend
Environment="PATH=/home/ubuntu/silica-client/silica-auth-server/backend/venv/bin"
ExecStart=/home/ubuntu/silica-client/silica-auth-server/backend/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Store Service
```bash
sudo nano /etc/systemd/system/silica-store.service
```

```ini
[Unit]
Description=Silica Store Website
After=network.target silica-backend.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/silica-client/silica-auth-server/website
Environment="PATH=/home/ubuntu/silica-client/silica-auth-server/website/venv/bin"
ExecStart=/home/ubuntu/silica-client/silica-auth-server/website/venv/bin/python store.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Discord Bot Service
```bash
sudo nano /etc/systemd/system/silica-discord.service
```

```ini
[Unit]
Description=Silica Discord Bot
After=network.target silica-backend.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/silica-client/silica-auth-server/discord-bot
ExecStart=/usr/bin/node bot.js
Restart=always
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
```

## Step 8: Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable silica-backend silica-store silica-discord
sudo systemctl start silica-backend
sudo systemctl start silica-store
sudo systemctl start silica-discord

# Check status
sudo systemctl status silica-backend
sudo systemctl status silica-store
sudo systemctl status silica-discord
```

## Step 9: Configure Stripe

1. Log in to your Stripe Dashboard
2. Get your API keys from Developers > API keys
3. Set up webhook endpoint:
   - Go to Developers > Webhooks
   - Add endpoint: `https://your-domain.com/api/stripe-webhook`
   - Select events: `checkout.session.completed`
   - Copy the webhook signing secret

4. Update your `.env` files with the correct Stripe keys

## Step 10: Using Screen (Alternative to Systemd)

If you prefer using screen instead of systemd:

```bash
# Start backend
screen -S silica-backend
cd /home/ubuntu/silica-client/silica-auth-server/backend
source venv/bin/activate
python app.py
# Detach with Ctrl+A, D

# Start store
screen -S silica-store
cd /home/ubuntu/silica-client/silica-auth-server/website
source venv/bin/activate
python store.py
# Detach with Ctrl+A, D

# Start Discord bot
screen -S silica-discord
cd /home/ubuntu/silica-client/silica-auth-server/discord-bot
node bot.js
# Detach with Ctrl+A, D

# List screens
screen -ls

# Reattach to a screen
screen -r silica-backend
```

## Monitoring and Logs

```bash
# View logs
sudo journalctl -u silica-backend -f
sudo journalctl -u silica-store -f
sudo journalctl -u silica-discord -f

# Or if using screen
screen -r silica-backend
screen -r silica-store
screen -r silica-discord
```

## Troubleshooting

1. **Port already in use**: Kill the process using the port
   ```bash
   sudo lsof -i :5000
   sudo lsof -i :8000
   sudo kill -9 <PID>
   ```

2. **Permission errors**: Ensure proper file ownership
   ```bash
   sudo chown -R ubuntu:ubuntu /home/ubuntu/silica-client
   ```

3. **Database errors**: Check database permissions
   ```bash
   chmod 666 /home/ubuntu/silica-client/silica-auth-server/backend/users.db
   chmod 666 /home/ubuntu/silica-client/silica-auth-server/website/purchases.db
   ```

## Security Recommendations

1. Use a firewall
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

2. Keep your system updated
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

3. Use strong passwords for all services
4. Regularly backup your databases
5. Monitor your logs for suspicious activity

## Final Notes

- The store is now accessible at: `https://your-domain.com`
- Backend API runs on: `http://localhost:5000`
- Make sure to configure your Discord bot permissions correctly
- Test the complete purchase flow before going live
- Set up proper email service for sending credentials (optional)

For support, join our Discord server! 