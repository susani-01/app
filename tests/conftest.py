from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from src.db.session import SessionLocal
from src.main import app


@pytest.fixture(scope="session")
def database_ready() -> bool:
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
            count = session.execute(
                text("SELECT COUNT(*) FROM quantity_item"),
            ).scalar_one()
            return count > 0
    except Exception:
        return False


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def require_database(database_ready: bool) -> None:
    if not database_ready:
        pytest.skip("Database not available or empty — run make setup first")
