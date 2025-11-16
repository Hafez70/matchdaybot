#!/bin/bash
# FIFA Bot - Stop Script (cPanel Optimized)

cd "$(dirname "$0")"

echo "🛑 Stopping FIFA Match Tracker Bot..."

# Check if PID file exists
if [ -f bot.pid ]; then
    BOT_PID=$(cat bot.pid)
    
    # Check if process is running
    if ps -p $BOT_PID > /dev/null 2>&1; then
        echo "Stopping bot (PID: $BOT_PID)..."
        kill $BOT_PID
        
        # Wait for process to stop
        for i in {1..10}; do
            if ! ps -p $BOT_PID > /dev/null 2>&1; then
                echo "✅ Bot stopped successfully"
                rm bot.pid
                exit 0
            fi
            sleep 1
        done
        
        # Force kill if still running
        echo "Bot didn't stop gracefully, forcing..."
        kill -9 $BOT_PID 2>/dev/null
        rm bot.pid
        echo "✅ Bot force stopped"
    else
        echo "⚠️  Bot not running (PID $BOT_PID not found)"
        rm bot.pid
    fi
else
    echo "⚠️  No PID file found"
    
    # Try to find and kill any running instance
    if pgrep -f "python.*main.py" > /dev/null; then
        echo "Found running bot process, stopping it..."
        pkill -f "python.*main.py"
        sleep 2
        echo "✅ Bot stopped"
    else
        echo "ℹ️  No bot process found"
    fi
fi
