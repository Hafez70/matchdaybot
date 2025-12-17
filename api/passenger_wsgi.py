"""
Passenger WSGI wrapper for FastAPI on cPanel
"""
import os
import sys

# Setup logging FIRST
import logging
LOG_FILE = '/home/fcfun/logs/passenger_debug.log'
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE)]
)
logger = logging.getLogger('passenger')
logger.info("=== Passenger WSGI Starting ===")

# Setup API directory path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
logger.info(f"Current dir: {current_dir}")
logger.info(f"sys.path: {sys.path[:3]}")

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
    logger.info("Loaded config.env")

# Import FastAPI app
logger.info("Importing main app...")
from main import app
logger.info("Main app imported successfully")

# Wrap ASGI app (FastAPI) to WSGI for Passenger
logger.info("Creating ASGI middleware...")
from a2wsgi import ASGIMiddleware

class LoggingMiddleware:
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '/')
        method = environ.get('REQUEST_METHOD', 'GET')
        logger.info(f"REQUEST: {method} {path}")
        try:
            result = self.app(environ, start_response)
            logger.info(f"RESPONSE OK for {path}")
            return result
        except Exception as e:
            logger.error(f"ERROR on {path}: {type(e).__name__}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

application = LoggingMiddleware(ASGIMiddleware(app))
logger.info("=== Passenger WSGI Ready ===")
