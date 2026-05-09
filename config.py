import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    
class DatabaseConfig:
    """Database configuration for Aiven Cloud MySQL."""
    # Option 1: Use Aiven connection string (recommended for cloud)
    DB_URL = os.getenv('DATABASE_URL', None)
    
    # Option 2: Use individual connection parameters
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'mysql.c.skillbridge.aivencloud.com')
    MYSQL_USER = os.getenv('MYSQL_USER', 'avnadmin')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'defaultdb')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 21513))
    
    # SSL Configuration for Aiven (recommended)
    USE_SSL = os.getenv('MYSQL_USE_SSL', 'true').lower() == 'true'
    SSL_CA_PATH = os.getenv('MYSQL_SSL_CA_PATH', './ca.pem')  # Path to CA certificate

config = Config()
db_config = DatabaseConfig()
