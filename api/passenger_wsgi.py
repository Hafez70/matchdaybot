"""
Passenger WSGI/ASGI wrapper for FastAPI
This file allows cPanel's Passenger to run FastAPI
"""
import sys
import os

# Add the api directory to path
api_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, api_dir)
os.chdir(api_dir)

# Load environment variables
from dotenv import load_dotenv
config_path = os.path.join(api_dir, '..', 'config.env')
load_dotenv(config_path)

# Import FastAPI app
from main import app

# Passenger ASGI application
application = app

