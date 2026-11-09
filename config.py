import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'marketmate-super-secret-key-change-in-production')
    DATABASE_PATH = os.environ.get('DATABASE_PATH', str(BASE_DIR / 'marketmate.db'))
    STORE_NAME = os.environ.get('STORE_NAME', 'MarketMate Grocery Store')
    STORE_ADDRESS = os.environ.get('STORE_ADDRESS', '45 Market Street, Suite 100, Metro City')
    STORE_PHONE = os.environ.get('STORE_PHONE', '+1 (555) 234-5678')
    STORE_EMAIL = os.environ.get('STORE_EMAIL', 'contact@marketmate.store')
    CURRENCY_SYMBOL = os.environ.get('CURRENCY_SYMBOL', '$')
    DEFAULT_TAX_RATE = float(os.environ.get('DEFAULT_TAX_RATE', '5.0'))  # 5% default sales tax
    TESTING = False
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    DATABASE_PATH = str(BASE_DIR / 'marketmate_test.db')
    SECRET_KEY = 'test-secret-key'

class ProductionConfig(Config):
    DEBUG = False

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
