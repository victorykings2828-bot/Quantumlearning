"""Guest session issue, resolution, and renewal.

The browser holds an opaque random token in an HttpOnly cookie. Only its
SHA-256 hash is stored, so a database read cannot reconstruct a usable
credential. Identity is never taken from a browser-supplied principal id.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.storage.models import GuestSession, Principal

SESSION_COOKIE_NAME = "qll_session"
CSRF_COOKIE_NAME = "qll_csrf"
CSRF_HEADER_NAME = "x-qll-csrf"

_TOKEN_BYTES = 32
_RENEW_WHEN_REMAINING = timedelta(days=7)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class IssuedSession:
    principal_id: str
    session_token: str
    csrf_token: str
    expires_at: datetime


@dataclass(frozen=True)
class ResolvedSession:
    principal_id: str
    session_id: str
    csrf_token: str
    expires_at: datetime
    renewed: bool


def create_guest(session: Session) -> IssuedSession:
    settings = get_settings()
    principal = Principal(kind="guest")
    session.add(principal)
    session.flush()

    token = secrets.token_urlsafe(_TOKEN_BYTES)
    csrf = secrets.token_urlsafe(_TOKEN_BYTES)
    expires_at = datetime.now(UTC) + timedelta(days=settings.session_ttl_days)
    record = GuestSession(
        principal_id=principal.id,
        token_hash=hash_token(token),
        csrf_token=csrf,
        expires_at=expires_at,
    )
    session.add(record)
    session.flush()
    return IssuedSession(
        principal_id=str(principal.id),
        session_token=token,
        csrf_token=csrf,
        expires_at=expires_at,
    )


def resolve(session: Session, token: str | None) -> ResolvedSession | None:
    if not token:
        return None
    record = session.scalar(
        select(GuestSession).where(GuestSession.token_hash == hash_token(token))
    )
    if record is None or record.revoked_at is not None:
        return None
    now = datetime.now(UTC)
    if record.expires_at <= now:
        return None

    renewed = False
    settings = get_settings()
    if record.expires_at - now < _RENEW_WHEN_REMAINING:
        record.expires_at = now + timedelta(days=settings.session_ttl_days)
        renewed = True
    record.last_seen_at = now
    session.flush()
    return ResolvedSession(
        principal_id=str(record.principal_id),
        session_id=str(record.id),
        csrf_token=record.csrf_token,
        expires_at=record.expires_at,
        renewed=renewed,
    )


def revoke(session: Session, session_id: str) -> None:
    record = session.get(GuestSession, session_id)
    if record is not None:
        record.revoked_at = datetime.now(UTC)
        session.flush()
