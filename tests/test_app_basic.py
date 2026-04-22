import os
import pytest
from app import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_index(client):
    r = client.get('/')
    assert r.status_code == 200
    assert b'INQ Project' in r.data or b'Welcome to INQ' in r.data

def test_about(client):
    r = client.get('/about')
    assert r.status_code == 200
    assert b'About' in r.data

def test_health(client):
    r = client.get('/health')
    assert r.status_code == 200
    assert r.is_json
    assert r.get_json().get('status') == 'ok'

def test_404(client):
    r = client.get('/this-page-does-not-exist')
    assert r.status_code in (404,)
