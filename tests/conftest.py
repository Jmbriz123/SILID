"""Unit tests never contact weather services or PostgreSQL."""

import psycopg2
import pytest
import requests


@pytest.fixture(autouse=True)
def block_external_services(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Unexpected external service call in an offline test")

    monkeypatch.setattr(requests.sessions.Session, "request", blocked)
    monkeypatch.setattr(psycopg2, "connect", blocked)


@pytest.fixture
def database_env():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "silid",
        "DB_USER": "silid_app",
        "DB_PASSWORD": "test-only:p@ss/$word",
    }
