# Silica Client Store System

A complete e-commerce solution for selling Silica Client licenses with Discord integration and Stripe payment processing.

## Features

- 🛍️ Modern, responsive store website
- 💳 Secure Stripe payment integration
- 🤖 Discord bot for license management
- 🔐 Automated account creation and activation
- 📊 Purchase tracking and management
- 🎫 Support for lifetime and monthly licenses

## System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Store Website │────▶│  Backend API    │◀────│  Discord Bot    │
│   (Port 8000)   │     │  (Port 5000)    │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                         │
         ▼                       ▼                         ▼
    ┌─────────┐           ┌──────────┐             ┌───────────┐
    │ Stripe  │           │ Users DB │             │  Discord  │
    └─────────┘           └──────────┘             └───────────┘
```

## Quick Start

1. **Clone the repository**
   ```bash
   git clone [your-repo-url]
   cd silica-client/silica-auth-server
   ```

2. **Run the setup script**
   ```bash
   chmod +x setup-env.sh
   ./setup-env.sh
   ```

3. **Install dependencies**
   ```bash
   # Backend
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cd ..

   # Website
   cd website
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cd ..

   # Discord Bot
   cd discord-bot
   npm install
   cd ..
   ```

4. **Start the services**
   ```bash
   # Terminal 1: Backend
   cd backend && source venv/bin/activate && python app.py

   # Terminal 2: Store
   cd website && source venv/bin/activate && python store.py

   # Terminal 3: Discord Bot
   cd discord-bot && node bot.js
   ```

5. **Access the store**
   - Store: http://localhost:8000
   - Backend API: http://localhost:5000

## Configuration

### Stripe Setup

1. Create a Stripe account at https://stripe.com
2. Get your API keys from the Dashboard
3. Create a webhook endpoint:
   - URL: `https://your-domain.com/api/stripe-webhook`
   - Events: `checkout.session.completed`
4. Update your `.env` files with the keys

### Discord Bot Setup

1. Create a Discord application at https://discord.com/developers
2. Add a bot to your application
3. Copy the bot token
4. Invite the bot to your server with appropriate permissions
5. Update the `.env` file with your bot token and server details

## API Endpoints

### Store Endpoints
- `GET /` - Homepage
- `GET /purchase` - Purchase page
- `POST /api/create-checkout-session` - Create Stripe checkout
- `POST /api/stripe-webhook` - Stripe webhook handler
- `GET /success` - Payment success page
- `GET /cancel` - Payment cancelled page

### Backend Endpoints
- `POST /auth/register` - Register new user
- `POST /auth/activate` - Activate user account (admin)
- `POST /auth/login` - User login
- `POST /auth/purchase-complete` - Handle purchase completion
- `GET /auth/users` - List all users (admin)
- `POST /auth/reset-hwid` - Reset hardware ID (admin)

## Discord Bot Commands

### User Commands
- `!register <email>` - Register a new account
- `!help` - Show help message

### Admin Commands
- `!activate <email> <days>` - Activate a user account
- `!add-duration <email> <days>` - Add subscription days
- `!remove-duration <email> <days>` - Remove subscription days
- `!reset-hwid <email>` - Reset user's hardware ID
- `!reset-account <email>` - Reset user account
- `!user-info <email>` - Get user information
- `!list-users` - List all registered users

## Payment Flow

1. User visits store and selects a plan
2. User enters Discord username and email
3. User is redirected to Stripe checkout
4. After successful payment:
   - Stripe webhook triggers
   - Account is automatically created
   - User receives credentials via email/Discord
   - Account is activated with appropriate duration

## Security Features

- HWID (Hardware ID) locking
- 2FA with Google Authenticator
- Secure password generation
- Admin-only endpoints protection
- Stripe webhook signature verification

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Find process using port
   lsof -i :5000  # or :8000
   # Kill the process
   kill -9 <PID>
   ```

2. **Database permission errors**
   ```bash
   chmod 666 backend/users.db
   chmod 666 website/purchases.db
   ```

3. **Module not found errors**
   - Make sure you're in the virtual environment
   - Reinstall dependencies: `pip install -r requirements.txt`

4. **Stripe webhook not working**
   - Check webhook signing secret
   - Ensure webhook URL is accessible
   - Check Stripe dashboard for webhook logs

## Production Deployment

See `STORE_DEPLOYMENT_GUIDE.md` for detailed production deployment instructions.

## License Pricing

- **Monthly License**: $5.00 (30 days)
- **Lifetime License**: $20.00 (1000 days)

## Support

For support, join our Discord server or open an issue on GitHub.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Credits

Built with:
- Flask (Python web framework)
- Stripe (Payment processing)
- Discord.js (Discord bot)
- Bootstrap (UI framework) 