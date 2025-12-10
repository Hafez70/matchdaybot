#!/bin/bash
# FIFA Bot - Restart Script (cPanel Optimized)

cd "$(dirname "$0")"

echo "🔄 Restarting FIFA Match Tracker Bot..."

# Stop the bot
./stop.sh

# Wait a moment
echo "Waiting 3 seconds..."
sleep 3

# Start the bot
./start.sh

