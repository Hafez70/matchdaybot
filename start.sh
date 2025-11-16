#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if we should run migration
if [ "$1" = "--migrate" ]; then
    echo "Running migration..."
    python3 migrate_data.py
fi

# Start the bot (use main.py for new modular version, bot.py for old version)
if [ "$1" = "--old" ]; then
    echo "Starting old version..."
    python3 bot.py
else
    echo "Starting new modular version..."
    python3 main.py
fi
