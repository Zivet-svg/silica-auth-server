#!/bin/bash

echo "🚀 Setting up Silica Authentication Server..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+"
    exit 1
fi

echo "✅ Dependencies check passed"

# Setup backend
echo "🔧 Setting up backend..."
cd backend
cp .env.example .env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "✅ Backend setup complete"

# Setup Discord bot
echo "🤖 Setting up Discord bot..."
cd ../discord-bot
cp .env.example .env
npm install
echo "✅ Discord bot setup complete"

cd ..

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your configuration"
echo "2. Edit discord-bot/.env with your bot token and server ID"
echo "3. Run the services:"
echo "   - Backend: cd backend && source venv/bin/activate && python app.py"
echo "   - Discord Bot: cd discord-bot && npm start"
echo ""
echo "Or use Docker: docker-compose up" 