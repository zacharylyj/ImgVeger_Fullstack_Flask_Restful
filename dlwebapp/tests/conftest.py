import os
import sys
import pytest
os.environ['FLASK_ENV'] = 'test'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from application import app, db, login_manager
from application.models import User, History

@pytest.fixture
def test_client():
    testing_client = app.test_client()
    ctx = app.app_context()
    ctx.push()
    yield testing_client
    ctx.pop()

@pytest.fixture
def init_database():
    db.create_all()
    db.session.commit()
    yield db
    db.session.remove()
    db.drop_all()

def pytest_sessionfinish(session, exitstatus):
    db_path = "instance/testdatabase.db"
    if os.path.exists(db_path):
        os.remove(db_path)