"""FastAPI dependencies that resolve and protect the guest principal."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.identity import sessions
from app.storage.database import db_session

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


@dataclass(frozen=True)
class Principal:
    id: str
    session_id: str


def set_session_cookies(response: Response, issued: sessions.IssuedSession) -> None:
    settings = get_settings()
    max_age = settings.session_ttl_days * 24 * 3600
    response.set_cookie(
        sessions.SESSION_COOKIE_NAME,
        issued.session_token,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    # Readable by the app so it can echo the value in the CSRF header.
    response.set_cookie(
        sessions.CSRF_COOKIE_NAME,
        issued.csrf_token,
        max_age=max_age,
        httponly=False,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def clear_session_cookies(response: Response) -> None:
    response.delete_cookie(sessions.SESSION_COOKIE_NAME, path="/")
    response.delete_cookie(sessions.CSRF_COOKIE_NAME, path="/")


def _origin_allowed(request: Request) -> bool:
    origin = request.headers.get("origin")
    if origin is None:
        # Same-origin non-CORS requests may omit Origin; fall back to Referer.
        referer = request.headers.get("referer")
        if referer is None:
            return True
        parsed = urlparse(referer)
        origin = f"{parsed.scheme}://{parsed.netloc}"
    allowed = {value.rstrip("/") for value in get_settings().allowed_origins}
    return origin.rstrip("/") in allowed


def require_principal(
    request: Request,
    session: Session = Depends(db_session),
) -> Principal:
    """Resolve the guest from the session cookie and enforce CSRF on mutations."""
    token = request.cookies.get(sessions.SESSION_COOKIE_NAME)
    resolved = sessions.resolve(session, token)
    if resolved is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "no_guest_session",
                "message": "No active guest session. Start a session to continue.",
            },
        )
    if request.method not in SAFE_METHODS:
        if not _origin_allowed(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "bad_origin", "message": "Request origin is not allowed."},
            )
        supplied = request.headers.get(sessions.CSRF_HEADER_NAME)
        if not supplied or supplied != resolved.csrf_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "csrf_failed",
                    "message": "Missing or invalid CSRF token for a state-changing request.",
                },
            )
    session.commit()
    return Principal(id=resolved.principal_id, session_id=resolved.session_id)


def optional_principal(
    request: Request,
    session: Session = Depends(db_session),
) -> Principal | None:
    token = request.cookies.get(sessions.SESSION_COOKIE_NAME)
    resolved = sessions.resolve(session, token)
    if resolved is None:
        return None
    session.commit()
    return Principal(id=resolved.principal_id, session_id=resolved.session_id)
