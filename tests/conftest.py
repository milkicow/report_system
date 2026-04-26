import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def reset_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(reset_db):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session(reset_db):
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def registered_user(client):
    resp = client.post(
        "/auth/register",
        json={
            "name": "Test Manager",
            "email": "manager@test.com",
            "password": "testpass123",
            "role": "manager",
        },
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def auth_headers(client, registered_user):
    resp = client.post(
        "/auth/token",
        data={
            "username": "manager@test.com",
            "password": "testpass123",
        },
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def dev_user(client, auth_headers):
    resp = client.post(
        "/users/",
        json={
            "name": "Dev User",
            "email": "dev@test.com",
            "password": "devpass123",
            "role": "developer",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def test_project(client, auth_headers):
    resp = client.post(
        "/projects/",
        json={
            "name": "Test Project",
            "budget_hours": 100.0,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()
