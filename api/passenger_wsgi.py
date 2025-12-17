"""
Minimal Passenger WSGI wrapper for FastAPI
"""
import os
import sys

# Write a marker file to prove this script runs
marker_file = "/home/fcfun/fifa-bot/api/PASSENGER_WAS_HERE.txt"
with open(marker_file, "w") as f:
    f.write(f"Passenger started at: {__import__('datetime').datetime.now()}\n")
    f.write(f"Python: {sys.executable}\n")
    f.write(f"Path: {sys.path}\n")

try:
    # Add current directory to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    os.chdir(current_dir)

    # Load environment variables from config.env
    config_path = os.path.join(current_dir, '..', 'config.env')
    if os.path.exists(config_path):
        with open(config_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

    # Import FastAPI app
    from main import app

    # Convert ASGI to WSGI
    from a2wsgi import ASGIMiddleware
    application = ASGIMiddleware(app)

    with open(marker_file, "a") as f:
        f.write("SUCCESS: App loaded!\n")

except Exception as e:
    import traceback
    with open(marker_file, "a") as f:
        f.write(f"ERROR: {e}\n")
        f.write(traceback.format_exc())
    raise
