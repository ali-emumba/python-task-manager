import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import get_db
from app.models.user import User, UserRole, Base  # include Base here
from app.models.task import Task
from app.core.security import get_password_hash

TEST_DB_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base.metadata.create_all(bind=engine)

# Dependency override
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def user_token_headers(client):
    email = "user@example.com"
    password = "password123"
    client.post("/auth/register", json={"email": email, "password": password})
    resp = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_token_headers(client):
    email = "admin@example.com"
    password = "password123"
    client.post("/auth/register", json={"email": email, "password": password})
    # elevate role
    db = TestingSessionLocal()
    admin_user = db.query(User).filter(User.email == email).first()
    admin_user.role = UserRole.admin  # type: ignore
    db.add(admin_user)
    db.commit()
    db.close()
    resp = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
