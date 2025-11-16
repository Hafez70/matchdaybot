#!/bin/bash

# Check if bot is running
if ! pgrep -f "python.*bot.py" > /dev/null; then
    echo "$(date): Bot is not running. Starting..."
    cd /home/xqaebsls/matchdaybot
    nohup python3 bot.py > bot.log 2>&1 &
    echo "$(date): Bot restarted. PID: $!"
fi

