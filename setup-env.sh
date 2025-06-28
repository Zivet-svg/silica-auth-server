#!/bin/bash

echo "🚀 Silica Client Store Environment Setup"
echo "======================================="

# Generate random keys
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
ADMIN_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

echo ""
echo "Generated Keys:"
echo "SECRET_KEY: $SECRET_KEY"
echo "ADMIN_KEY: $ADMIN_KEY"
echo ""

# Backend .env
echo "Creating backend/.env..."
cat > backend/.env << EOL
SECRET_KEY=$SECRET_KEY
ADMIN_KEY=$ADMIN_KEY
HOST=0.0.0.0
PORT=5000
EOL

# Website .env
echo "Creating website/.env..."
echo ""
echo "Please enter your Stripe configuration:"
read -p "Stripe Secret Key (sk_live_...): " STRIPE_SECRET_KEY
read -p "Stripe Webhook Secret (whsec_...): " STRIPE_WEBHOOK_SECRET

cat > website/.env << EOL
SECRET_KEY=$SECRET_KEY
STRIPE_SECRET_KEY=$STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET=$STRIPE_WEBHOOK_SECRET
BACKEND_URL=http://localhost:5000
ADMIN_KEY=$ADMIN_KEY
STORE_HOST=0.0.0.0
STORE_PORT=8000
EOL

# Discord bot .env
echo ""
echo "Creating discord-bot/.env..."
echo "Please enter your Discord bot configuration:"
read -p "Discord Bot Token: " DISCORD_TOKEN
read -p "Admin Role ID (optional): " ADMIN_ROLE_ID
read -p "Allowed Role ID (optional): " ALLOWED_ROLE_ID
read -p "Allowed Channel IDs (comma-separated, optional): " ALLOWED_CHANNELS
read -p "Authorized Server ID (optional): " AUTHORIZED_SERVER_ID

cat > discord-bot/.env << EOL
DISCORD_TOKEN=$DISCORD_TOKEN
BACKEND_URL=http://localhost:5000
ADMIN_KEY=$ADMIN_KEY
ADMIN_ROLE_ID=$ADMIN_ROLE_ID
ALLOWED_ROLE_ID=$ALLOWED_ROLE_ID
ALLOWED_CHANNELS=$ALLOWED_CHANNELS
AUTHORIZED_SERVER_ID=$AUTHORIZED_SERVER_ID
EOL

echo ""
echo "✅ Environment files created successfully!"
echo ""
echo "Important: Save this ADMIN_KEY for future reference:"
echo "$ADMIN_KEY"
echo ""
echo "Next steps:"
echo "1. Install dependencies in each directory"
echo "2. Start the services"
echo "3. Configure Stripe webhook in your Stripe dashboard" 