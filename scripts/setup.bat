@echo off
echo 🚀 Setting up Silica Authentication Server...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.11+
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js 18+
    pause
    exit /b 1
)

echo ✅ Dependencies check passed

REM Setup backend
echo 🔧 Setting up backend...
cd backend
copy .env.example .env
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo ✅ Backend setup complete

REM Setup Discord bot  
echo 🤖 Setting up Discord bot...
cd ..\discord-bot
copy .env.example .env
npm install
echo ✅ Discord bot setup complete

cd ..

echo.
echo 🎉 Setup complete!
echo.
echo Next steps:
echo 1. Edit backend\.env with your configuration
echo 2. Edit discord-bot\.env with your bot token and server ID
echo 3. Run the services:
echo    - Backend: cd backend ^&^& venv\Scripts\activate.bat ^&^& python app.py
echo    - Discord Bot: cd discord-bot ^&^& npm start
echo.
echo Or use Docker: docker-compose up
pause 