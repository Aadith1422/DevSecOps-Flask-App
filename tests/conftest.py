import os
import tempfile
from pathlib import Path

import pytest

# Configure the test database before importing app.py
_test_dir = tempfile.TemporaryDirectory()

os.environ["DATABASE_URL"] = (
    "sqlite:///" + str(Path(_test_dir.name) / "test_students.db")
)

from app import app
from models import db


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        db.drop_all()
        db.create_all()

        with app.test_client() as test_client:
            yield test_client

        db.session.remove()