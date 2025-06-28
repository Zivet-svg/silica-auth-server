# Discord Webhook Integration Setup

## 🎯 What This Does
When someone purchases on your website, it now **automatically triggers your Discord bot** to send them login credentials via DM - exactly like when they type `!register` in Discord.

## 🚀 Quick Setup on Your VPS

### Option 1: Git Pull (Recommended)
```bash
cd /path/to/your/discord-bot
git pull origin main
npm install express
pm2 restart bot  # or however you restart your bot
```

### Option 2: Auto-Update Script
```bash
# Download and run the auto-update script
curl -s https://raw.githubusercontent.com/Zivet-svg/silica-auth-server/main/discord-bot/update-bot.sh | bash
```

## 🔧 Configuration

Make sure your Discord bot has these environment variables:
```bash
WEBHOOK_PORT=3001  # Port for webhook server (default: 3001)
DISCORD_TOKEN=your_bot_token
BACKEND_URL=http://67.205.158.33:5000
```

## 📋 How It Works

1. **Customer purchases** on website
2. **Website calls** `/auth/trigger-discord-register` 
3. **Backend creates** inactive account with credentials
4. **Backend calls** Discord bot webhook at `localhost:3001/webhook/register`
5. **Discord bot finds** user by username and **sends DM** with:
   - Login credentials
   - QR code for 2FA
   - Setup instructions
6. **Admin still needs** to activate account with `!activate` after verifying payment

## ✅ Success Messages

- **DM sent**: "Registration complete! Check your Discord DMs for login credentials."
- **DM failed**: "Account created but could not send Discord DM. Contact admin for credentials."
- **Bot offline**: "Account created but Discord bot is offline. Contact admin for credentials."

## 🔍 Testing

1. Go to your website purchase page
2. Enter a Discord username that exists in your server
3. Submit purchase
4. Check if that user receives a DM with credentials
5. Check bot console for success/error messages

## 📝 Notes

- Bot searches for users by: `username`, `displayName`, or `tag` (case insensitive)
- User must be in a server where your bot has access
- User must have DMs enabled from server members
- Account is created as **inactive** - admin must still use `!activate` after payment verification

## 🐛 Troubleshooting

- **"Discord user not found"**: User not in any server with your bot, or username doesn't match
- **"Could not send DM"**: User has DMs disabled from server members
- **"Webhook processing failed"**: Check bot console logs for detailed error

The system now perfectly mimics the `!register` Discord command flow! 