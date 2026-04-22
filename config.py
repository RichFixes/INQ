import os
class BaseConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'replace-me')
    DEBUG = False
    TESTING = False

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV = 'development'

class ProductionConfig(BaseConfig):
    ENV = 'production'

class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
