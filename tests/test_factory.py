from app import create_app
from config import TestingConfig

def test_create_app():
    app = create_app(config_class=TestingConfig)
    assert app is not None
    assert app.config['TESTING'] is True
