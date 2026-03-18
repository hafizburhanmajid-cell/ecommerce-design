import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Secret Key for Sessions & Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')
    
    # Database Configuration (Match your .env variables)
    MYSQL_HOST = os.environ.get('DB_HOST', 'localhost')
    MYSQL_USER = os.environ.get('DB_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('DB_PASSWORD', 'Emaan123')
    MYSQL_DB = os.environ.get('DB_NAME', 'ecommerce_db')
    
    # Flask Configuration
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'True')
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Upload Configuration (if needed)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')