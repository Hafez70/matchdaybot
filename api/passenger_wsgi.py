"""
Passenger WSGI wrapper for FastAPI on cPanel
"""
import os
import sys

# Activate virtual environment
VENV_PATH = '/home/fcfun/fifa-bot/venv'
python_path = os.path.join(VENV_PATH, 'lib', 'python3.11', 'site-packages')
if os.path.exists(python_path) and python_path not in sys.path:
    sys.path.insert(0, python_path)

# Prevent recursion - only run once
if 'main' not in sys.modules:
    # Setup paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Change to API directory
    os.chdir(current_dir)
    
    # Load environment
    os.environ.setdefault('BOT_TOKEN', '')
    
    # Load .env file
    config_path = os.path.join(current_dir, '..', 'config.env')
    if os.path.exists(config_path):
        with open(config_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Import after setup
from main import app
application = app

