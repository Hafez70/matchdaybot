#!/bin/bash
# FIFA Bot - Status Check Script

cd "$(dirname "$0")"

echo "📊 FIFA Match Tracker Bot - Status"
echo "===================================="
echo ""

# Check if bot is running
if [ -f bot.pid ]; then
    BOT_PID=$(cat bot.pid)
    
    if ps -p $BOT_PID > /dev/null 2>&1; then
        echo "Status: ✅ RUNNING"
        echo "PID: $BOT_PID"
        
        # Get process info
        echo ""
        echo "Process Info:"
        ps -p $BOT_PID -o pid,ppid,%cpu,%mem,etime,command
        
        # Check memory usage
        echo ""
        echo "Memory Usage:"
        ps -p $BOT_PID -o rss= | awk '{printf "%.2f MB\n", $1/1024}'
        
    else
        echo "Status: ❌ NOT RUNNING"
        echo "Warning: PID file exists but process not found"
        echo "PID in file: $BOT_PID"
    fi
else
    if pgrep -f "python.*main.py" > /dev/null; then
        echo "Status: ⚠️  RUNNING (no PID file)"
        echo "Process:"
        pgrep -f "python.*main.py" | while read pid; do
            ps -p $pid -o pid,ppid,%cpu,%mem,etime,command
        done
    else
        echo "Status: ❌ NOT RUNNING"
    fi
fi

# Show last log entries
if [ -f bot.log ]; then
    echo ""
    echo "Last 5 Log Entries:"
    echo "-------------------"
    tail -5 bot.log
fi

# Show keep_alive log if exists
if [ -f keep_alive.log ]; then
    echo ""
    echo "Last Keep-Alive Check:"
    echo "----------------------"
    tail -1 keep_alive.log
fi

echo ""
echo "Commands:"
echo "  ./start.sh   - Start bot"
echo "  ./stop.sh    - Stop bot"
echo "  ./restart.sh - Restart bot"
echo "  tail -f bot.log - View live logs"

