FROM node:18-slim

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 discordbot

# Change ownership to non-root user
RUN chown -R discordbot:nodejs /app
USER discordbot

# Start the bot
CMD ["npm", "start"] 