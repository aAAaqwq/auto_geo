# -*- coding: utf-8 -*-
"""
用户管理API测试
"""

from contextlib import contextmanager
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import Base, get_db
from backend.database.models import User
from backend.services.password import hash_password


def setup_test_db() -> sessionmaker:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    TestingSessionLocal = setup_test_db()
    app.state.testing_session_local = TestingSessionLocal

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    app.state.testing_session_local = None


@contextmanager
def _get_session():
    TestingSessionLocal = app.state.testing_session_local
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _create_user(db, username: str, role: str = "user", status: str = "active") -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        role=role,
        status=status,
        password_hash=hash_password("password123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _login(client: TestClient, username: str, password: str = "password123") -> str:
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_admin_user_lifecycle(client: TestClient):
    with _get_session() as db:
        _create_user(db, "admin", role="admin")

    admin_token = _login(client, "admin")

    create_resp = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "user1",
            "email": "user1@example.com",
            "role": "user",
            "status": "active",
            "password": "initialPass123",
        },
    )
    assert create_resp.status_code == 200
    created = create_resp.json()
    assert created["username"] == "user1"
    assert created["role"] == "user"
    user_id = created["id"]

    list_resp = client.get("/api/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert list_resp.status_code == 200
    usernames = {item["username"] for item in list_resp.json()}
    assert {"admin", "user1"}.issubset(usernames)

    get_resp = client.get(f"/api/users/{user_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert get_resp.status_code == 200
    assert get_resp.json()["email"] == "user1@example.com"

    update_resp = client.put(
        f"/api/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "user1+updated@example.com",
            "role": "user",
            "status": "active",
            "password": "newPass123",
        },
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["email"] == "user1+updated@example.com"

    token = _login(client, "user1", password="newPass123")
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "user1"

    delete_resp = client.delete(
        f"/api/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert delete_resp.status_code == 200
    assert delete_resp.json()["success"] is True

    login_resp = client.post("/api/auth/login", json={"username": "user1", "password": "newPass123"})
    assert login_resp.status_code == 401


def test_non_admin_forbidden(client: TestClient):
    with _get_session() as db:
        _create_user(db, "user2", role="user")

    token = _login(client, "user2")
    resp = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "blocked",
            "email": "blocked@example.com",
            "role": "user",
            "status": "active",
            "password": "password123",
        },
    )
    assert resp.status_code == 403


def test_get_missing_user_returns_404(client: TestClient):
    with _get_session() as db:
        _create_user(db, "admin", role="admin")

    admin_token = _login(client, "admin")
    resp = client.get("/api/users/9999", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 404
