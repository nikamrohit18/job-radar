"""Clerk JWT validation — extracts the Clerk user ID from a Bearer token."""
import os

import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

_JWKS_URL = os.getenv("CLERK_JWKS_URL", "")
_jwks_client: PyJWKClient | None = None

_bearer = HTTPBearer()


def _client() -> PyJWKClient:
    global _jwks_client
    if not _JWKS_URL:
        raise HTTPException(status_code=500, detail="CLERK_JWKS_URL is not configured")
    if _jwks_client is None:
        _jwks_client = PyJWKClient(_JWKS_URL)
    return _jwks_client


def get_clerk_user_id(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
) -> str:
    """FastAPI dependency — validate Clerk JWT and return the Clerk user ID (sub claim)."""
    token = credentials.credentials
    try:
        signing_key = _client().get_signing_key_from_jwt(token)
        payload = jwt.decode(token, signing_key.key, algorithms=["RS256"])
        return payload["sub"]
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")
