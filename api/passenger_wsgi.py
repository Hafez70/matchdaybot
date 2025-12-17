"""
Passenger WSGI wrapper for FastAPI on cPanel
cPanel's Passenger handles the venv automatically via .htaccess
"""
import os
import sys

# Setup API directory path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

os.chdir(current_dir)

# Load config.env manually
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

# Wrap ASGI app (FastAPI) to WSGI for Passenger
from a2wsgi import ASGIMiddleware
application = ASGIMiddleware(app)
