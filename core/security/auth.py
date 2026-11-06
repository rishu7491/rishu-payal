"""Security and Authentication for Payal Core Engine.

Enforces local token-based authentication on sensitive API endpoints,
preventing unauthorized LAN or remote command execution.
"""

import os
from pathlib import Path
import secrets
from typing import Optional
from fastapi import Header, HTTPException, Request, status

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
TOKEN_FILE = DATA_DIR / "auth_token.secret"


def get_or_create_auth_token() -> str:
    """Retrieve persistent local auth token or create a cryptographically secure one."""
    env_token = os.environ.get("PAYAL_AUTH_TOKEN")
    if env_token and len(env_token.strip()) >= 16:
        return env_token.strip()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if TOKEN_FILE.exists():
        try:
            token = TOKEN_FILE.read_text(encoding="utf-8").strip()
            if len(token) >= 16:
                return token
        except Exception:
            pass

    # Generate high-entropy 256-bit token
    new_token = f"payal_sec_{secrets.token_hex(24)}"
    try:
        TOKEN_FILE.write_text(new_token, encoding="utf-8")
    except Exception:
        pass
    return new_token


AUTH_TOKEN = get_or_create_auth_token()


def verify_auth_token(
    request: Request,
    x_payal_token: Optional[str] = Header(None, alias="X-Payal-Token"),
    authorization: Optional[str] = Header(None),
) -> bool:
    """Verify that the request is authenticated with the Payal security token."""
    # 1. Check loopback / localhost requests (optional bypass for local development)
    client_host = request.client.host if request.client else ""
    if client_host in ("127.0.0.1", "::1", "localhost"):
        return True

    # 2. Check X-Payal-Token header
    if isinstance(x_payal_token, str) and secrets.compare_digest(x_payal_token.strip(), AUTH_TOKEN):
        return True

    # 3. Check Authorization: Bearer <token>
    if isinstance(authorization, str) and authorization.startswith("Bearer "):
        bearer_token = authorization.split("Bearer ", 1)[1].strip()
        if secrets.compare_digest(bearer_token, AUTH_TOKEN):
            return True

    # 4. Check query param for local webview or dev testing
    token_param = request.query_params.get("token")
    if token_param and secrets.compare_digest(token_param.strip(), AUTH_TOKEN):
        return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Valid Payal security token required for this operation.",
        headers={"WWW-Authenticate": "Bearer"},
    )
