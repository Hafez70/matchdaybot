#!/bin/bash
# FIFA Bot - Start Script (cPanel Optimized)

cd "$(dirname "$0")"

echo "🚀 Starting FIFA Match Tracker Bot..."

# Check if bot is already running
if [ -f bot.pid ]; then
    if ps -p $(cat bot.pid) > /dev/null 2>&1; then
        echo "⚠️  Bot is already running (PID: $(cat bot.pid))"
        echo "Use ./stop.sh first to stop it"
        exit 1
    else
        echo "Cleaning up stale PID file..."
        rm bot.pid
    fi
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  No virtual environment found, using system Python"
fi

# Check if config.env exists
if [ ! -f "config.env" ]; then
    echo "❌ Error: config.env not found!"
    echo "Create it from env_example.txt and add your bot token"
    exit 1
fi

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found!"
    exit 1
fi

# Start the bot in background
echo "Starting bot in background..."
nohup python3 main.py > bot.log 2>&1 &
BOT_PID=$!

# Save PID
echo $BOT_PID > bot.pid

# Wait a moment and check if it started successfully
sleep 2

if ps -p $BOT_PID > /dev/null 2>&1; then
    echo "✅ Bot started successfully!"
    echo "   PID: $BOT_PID"
    echo "   Log: tail -f bot.log"
else
    echo "❌ Bot failed to start. Check bot.log for errors:"
    tail -20 bot.log
    rm bot.pid 2>/dev/null
    exit 1
fi
