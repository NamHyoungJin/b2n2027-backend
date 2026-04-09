"""관리자 Refresh JWT — HttpOnly 쿠키."""
from __future__ import annotations

from django.conf import settings
from django.http import HttpResponse


def _admin_refresh_cookie_name() -> str:
    return getattr(settings, "ADMIN_JWT_REFRESH_COOKIE_NAME", "adminRefreshToken")


def _admin_refresh_cookie_domain():
    d = getattr(settings, "ADMIN_JWT_REFRESH_COOKIE_DOMAIN", None)
    if d is None or (isinstance(d, str) and not d.strip()):
        return None
    return d.strip() if isinstance(d, str) else d


def _normalize_samesite(raw) -> str:
    """Django set_cookie: 'Lax' | 'Strict' | 'None'. 크로스 서브도메인 시 None + Secure."""
    if raw is None:
        return "Lax"
    s = raw if isinstance(raw, str) else str(raw)
    key = s.strip().lower()
    if key == "none":
        return "None"
    if key == "strict":
        return "Strict"
    return "Lax"


def _cookie_secure(request, samesite: str) -> bool:
    override = getattr(settings, "ADMIN_JWT_REFRESH_COOKIE_SECURE", None)
    if override is True:
        return True
    if override is False:
        return False
    secure = bool(request.is_secure())
    if samesite == "None":
        return True
    return secure


def attach_admin_refresh_cookie(response: HttpResponse, request, refresh_token: str) -> None:
    if not refresh_token:
        return
    name = _admin_refresh_cookie_name()
    domain = _admin_refresh_cookie_domain()
    samesite = _normalize_samesite(getattr(settings, "ADMIN_JWT_REFRESH_COOKIE_SAMESITE", "Lax"))
    kwargs = {
        "key": name,
        "value": refresh_token,
        "max_age": int(settings.JWT_REFRESH_EXPIRATION_DELTA),
        "httponly": True,
        "secure": _cookie_secure(request, samesite),
        "samesite": samesite,
        "path": "/",
    }
    if domain:
        kwargs["domain"] = domain
    response.set_cookie(**kwargs)


def clear_admin_refresh_cookie(response: HttpResponse, request) -> None:
    name = _admin_refresh_cookie_name()
    domain = _admin_refresh_cookie_domain()
    if domain:
        response.delete_cookie(name, path="/", domain=domain)
    else:
        response.delete_cookie(name, path="/")
