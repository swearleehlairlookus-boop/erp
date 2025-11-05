import os
from datetime import timedelta

class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'palmed-clinic-secret-key-2025'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Database settings
    DB_HOST = os.environ.get('DB_HOST', 'db-polmed.mysql.database.azure.com')
    DB_NAME = os.environ.get('DB_NAME', 'mobile_clinic_erp')
    DB_USER = os.environ.get('DB_USER', 'dbadmin')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Polm3d!DB@2025')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    
    # JWT settings
    JWT_SECRET_KEY = SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    
    # Pagination settings
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Security settings
    BCRYPT_LOG_ROUNDS = 12
    
    # Offline sync settings
    SYNC_BATCH_SIZE = 100
    SYNC_TIMEOUT = 300  # 5 minutes

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DB_NAME = 'mobile_clinic_erp_test'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
