import os
from fastapi import HTTPException
from fastapi.testclient import TestClient
import pytest

from core.security.auth import AUTH_TOKEN, get_or_create_auth_token, verify_auth_token
from services.api.app import create_app


def test_auth_token_generation():
    token = get_or_create_auth_token()
    assert token is not None
    assert len(token) >= 16
    assert token.startswith("payal_sec_") or len(token) >= 16


def test_verify_auth_token_loopback():
    class DummyClient:
        host = "127.0.0.1"

    class DummyRequest:
        client = DummyClient()
        query_params = {}

    req = DummyRequest()
    assert verify_auth_token(req) is True


def test_verify_auth_token_header():
    class DummyClient:
        host = "192.168.1.100"

    class DummyRequest:
        client = DummyClient()
        query_params = {}

    req = DummyRequest()
    assert verify_auth_token(req, x_payal_token=AUTH_TOKEN) is True

    with pytest.raises(HTTPException) as exc:
        verify_auth_token(req, x_payal_token="invalid_token")
    assert exc.value.status_code == 401
