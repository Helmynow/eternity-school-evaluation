"""
Supabase JWT authentication helpers.

The frontend sends a Supabase access token as `Authorization: Bearer <jwt>`.
In production, the API should verify this JWT using the project's JWT secret.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from jose import JWTError, jwt


class SupabaseAuthError(Exception):
    """Raised when a Supabase JWT cannot be validated."""


@dataclass(frozen=True)
class AuthContext:
    email: str
    user_id: Optional[str]
    role: Optional[str]
    claims: Dict[str, Any]


def extract_bearer_token(authorization_header: Optional[str]) -> Optional[str]:
    if not authorization_header:
        return None
    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None


def decode_supabase_jwt(
    token: str,
    *,
    jwt_secret: str,
    audience: Optional[str] = "authenticated",
) -> AuthContext:
    """
    Decode and validate a Supabase access token.

    Supabase issues HS256 tokens signed with the project's JWT secret.
    """
    try:
        options = {"verify_aud": bool(audience)}
        claims = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            audience=audience if audience else None,
            options=options,
        )
    except JWTError as exc:
        raise SupabaseAuthError("Invalid or expired token") from exc

    email = claims.get("email")
    if not email:
        raise SupabaseAuthError("Token missing email claim")

    user_id = claims.get("sub")
    role = claims.get("role")
    return AuthContext(email=email, user_id=user_id, role=role, claims=claims)

