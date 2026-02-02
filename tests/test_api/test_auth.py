# -*- coding: utf-8 -*-
"""
认证与权限测试
"""

from typing import Generator
from contextlib import contextmanager

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


def _create_user(db, username: str, role: str = "user") -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        role=role,
        status="active",
        password_hash=hash_password("password123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@contextmanager
def _get_session():
    TestingSessionLocal = app.state.testing_session_local
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _login(client: TestClient, username: str, password: str = "password123") -> str:
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_login_and_me(client: TestClient):
    with _get_session() as db:
        _create_user(db, "admin", role="admin")

    token = _login(client, "admin")
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "admin"


def test_user_cannot_access_admin_routes(client: TestClient):
    with _get_session() as db:
        _create_user(db, "user1", role="user")

    token = _login(client, "user1")
    resp = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_owner_scope_for_accounts(client: TestClient):
    with _get_session() as db:
        _create_user(db, "user1", role="user")
        _create_user(db, "user2", role="user")

    token1 = _login(client, "user1")
    resp = client.post(
        "/api/accounts",
        headers={"Authorization": f"Bearer {token1}"},
        json={"platform": "zhihu", "account_name": "U1账号"},
    )
    assert resp.status_code == 201

    token2 = _login(client, "user2")
    resp = client.get("/api/accounts", headers={"Authorization": f"Bearer {token2}"})
    assert resp.status_code == 200
    assert resp.json() == []

    with _get_session() as db:
        _create_user(db, "admin", role="admin")
    admin_token = _login(client, "admin")
    resp = client.get("/api/accounts", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1
