#!/bin/bash

# Silica Discord Bot Auto-Update Script
echo "🤖 Updating Silica Discord Bot..."

# Backup current bot.js
cp bot.js bot.js.backup.$(date +%s)

# Download updated bot.js
echo "📥 Downloading updated bot.js..."
curl -o bot.js.new https://raw.githubusercontent.com/Zivet-svg/vercel-frontend/main/discord-bot/bot.js

if [ $? -eq 0 ]; then
    mv bot.js.new bot.js
    echo "✅ Bot updated successfully!"
    echo "🔄 Restarting bot..."
    
    # Kill existing bot process
    pkill -f "node bot.js"
    
    # Install express if not installed
    npm install express
    
    # Start bot in background
    nohup node bot.js > bot.log 2>&1 &
    
    echo "🚀 Bot restarted with webhook support!"
    echo "📋 Bot is now listening on port 3001 for website triggers"
else
    echo "❌ Failed to download update"
    exit 1
fi 