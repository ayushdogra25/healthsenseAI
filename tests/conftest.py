import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_healthsense.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["DEBUG"] = "true"
os.environ["GEMINI_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient

from backend.database.connection import Base, engine
from backend.main import app


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def user_payload():
    return {
        "full_name": "Admin User",
        "email": "admin@example.com",
        "password": "StrongPass1!",
        "confirm_password": "StrongPass1!",
    }


@pytest.fixture
def auth_headers(client, user_payload):
    client.post("/api/auth/register", json=user_payload)
    response = client.post(
        "/api/auth/login",
        json={"email": user_payload["email"], "password": user_payload["password"]},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def pytest_sessionfinish(session, exitstatus):
    engine.dispose()
    db_path = Path("test_healthsense.db")
    try:
        if db_path.exists():
            db_path.unlink()
    except PermissionError:
        pass
