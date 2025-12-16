"""
Passenger WSGI wrapper for FastAPI on cPanel
"""
import os
import sys

# FIRST: Activate virtual environment before ANY imports
VENV_PATH = '/home/fcfun/fifa-bot/venv'
site_packages = os.path.join(VENV_PATH, 'lib', 'python3.11', 'site-packages')
if os.path.exists(site_packages):
    sys.path.insert(0, site_packages)

# Setup API directory path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

os.chdir(current_dir)

# Load config.env manually (before importing dotenv)
config_path = os.path.join(current_dir, '..', 'config.env')
if os.path.exists(config_path):
    with open(config_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Now import FastAPI app
from main import app

# Wrap ASGI app (FastAPI) to WSGI for Passenger
from a2wsgi import ASGIMiddleware
application = ASGIMiddleware(app)
