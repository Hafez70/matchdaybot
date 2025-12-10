#!/bin/bash
# FIFA Bot - Keep Alive Script (cPanel Optimized)
# This script monitors and restarts the bot if it crashes
# Add to cPanel Cron Jobs: */5 * * * * ~/fifa-bot/keep_alive.sh

cd "$(dirname "$0")"

LOG_FILE="keep_alive.log"
MAX_LOG_SIZE=1048576  # 1MB

# Function to log with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

# Rotate log if too large
if [ -f "$LOG_FILE" ]; then
    LOG_SIZE=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null)
    if [ "$LOG_SIZE" -gt "$MAX_LOG_SIZE" ]; then
        mv $LOG_FILE ${LOG_FILE}.old
        log_message "Log rotated"
    fi
fi

# Check if bot is running
if [ -f bot.pid ]; then
    BOT_PID=$(cat bot.pid)
    
    if ps -p $BOT_PID > /dev/null 2>&1; then
        # Bot is running - log every hour only (check minute)
        MINUTE=$(date '+%M')
        if [ "$MINUTE" = "00" ] || [ "$MINUTE" = "30" ]; then
            log_message "✓ Bot is running (PID: $BOT_PID)"
        fi
        exit 0
    else
        # PID file exists but process not running
        log_message "⚠ Bot not running (stale PID: $BOT_PID), restarting..."
        rm bot.pid
    fi
else
    # No PID file - check if process exists anyway
    if pgrep -f "python.*main.py" > /dev/null; then
        log_message "⚠ Bot running without PID file, creating PID..."
        pgrep -f "python.*main.py" > bot.pid
        exit 0
    fi
    
    log_message "✗ Bot not running, starting..."
fi

# Start the bot
if [ -d "venv" ]; then
    source venv/bin/activate
fi

nohup python3 main.py > bot.log 2>&1 &
BOT_PID=$!
echo $BOT_PID > bot.pid

# Wait and verify startup
sleep 3

if ps -p $BOT_PID > /dev/null 2>&1; then
    log_message "✓ Bot started successfully (PID: $BOT_PID)"
else
    log_message "✗ Bot failed to start - check bot.log"
    # Log last error from bot.log
    if [ -f bot.log ]; then
        tail -5 bot.log >> $LOG_FILE
    fi
    rm bot.pid 2>/dev/null
fi
