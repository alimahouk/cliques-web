import os
from datetime import timedelta

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_env_var(key, default=None, required=True):
    """Get environment variable or raise exception if required and not found."""
    value = os.getenv(key, default)
    if required and value is None:
        raise ValueError(f"Environment variable {key} is required but not set")
    return value

# Flask Configuration
SECRET_KEY = get_env_var('FLASK_SECRET_KEY').encode()
SESSION_TYPE = get_env_var('FLASK_SESSION_TYPE', 'filesystem')
PERMANENT_SESSION_LIFETIME = timedelta(days=int(get_env_var('FLASK_PERMANENT_SESSION_LIFETIME', '30')))
SEND_FILE_MAX_AGE_DEFAULT = timedelta(hours=int(get_env_var('FLASK_SEND_FILE_MAX_AGE', '1')))

# Mail Configuration
MAIL_DEFAULT_SENDER = get_env_var('MAIL_DEFAULT_SENDER')
MAIL_USE_TLS = get_env_var('MAIL_USE_TLS', 'True').lower() == 'true'
MAIL_USERNAME = get_env_var('MAIL_USERNAME')
MAIL_PASSWORD = get_env_var('MAIL_PASSWORD')
MAIL_HOST = get_env_var('MAIL_HOST')

# Database Configuration
DB_CONFIG = {
    'host': get_env_var('DB_HOST', 'localhost'),
    'user': get_env_var('DB_USER'),
    'passwd': get_env_var('DB_PASSWORD'),
    'db': get_env_var('DB_NAME'),
    'charset': get_env_var('DB_CHARSET', 'utf8mb4')
}

# Application Configuration
APP_DOMAIN = get_env_var('APP_DOMAIN')
APP_SCHEME = get_env_var('APP_SCHEME', 'https') 