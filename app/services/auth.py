import hashlib
import hmac
import os
import uuid
from datetime import datetime, timedelta

from fastapi import Header, HTTPException
from sqlalchemy.orm import Session

from app.models import Group, SessionToken, User
from app.config import settings

ROLE_SUPERADMIN = "superadmin"
ROLE_ADMIN = "admin"
ROLE_USER = "gebruiker"


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    iterations = 200000
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${key.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algo, iter_raw, salt_hex, key_hex = password_hash.split("$")
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iter_raw)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), iterations)
        return hmac.compare_digest(key.hex(), key_hex)
    except Exception:
        return False


def issue_token(db: Session, user: User) -> str:
    token = f"tok_{uuid.uuid4().hex}{uuid.uuid4().hex}"
    expires_at = datetime.utcnow() + timedelta(days=max(1, int(getattr(settings, "session_ttl_days", 30) or 30)))
    db.add(SessionToken(token=token, user_id=user.id, tenant_id=user.tenant_id, expires_at=expires_at))
    db.commit()
    return token


def user_group_ids(user: User) -> list[str]:
    tenant_id = str(getattr(user, "active_tenant_id", None) or getattr(user, "tenant_id", "") or "")
    return [g.id for g in user.groups if str(getattr(g, "tenant_id", "") or "") == tenant_id]


def user_is_admin(user: User) -> bool:
    if user.is_bootstrap_admin:
        return True
    return any((g.name or "").strip().lower().startswith("administrators") for g in (user.groups or []))


def user_role(user: User) -> str:
    if user.is_bootstrap_admin:
        return ROLE_SUPERADMIN
    if user_is_admin(user):
        return ROLE_ADMIN
    return ROLE_USER


def user_to_out(user: User, tenant_name: str | None = None) -> dict:
    active_tenant = str(getattr(user, "active_tenant_id", None) or getattr(user, "tenant_id", "") or "")
    return {
        "id": user.id,
        "tenant_id": active_tenant,
        "tenant_name": tenant_name or "",
        "email": user.email,
        "name": user.name,
        "avatar_path": user.avatar_path,
        "role": user_role(user),
        "is_bootstrap_admin": user.is_bootstrap_admin,
        "is_admin": user_is_admin(user),
        "group_ids": user_group_ids(user),
    }


def group_to_out(group: Group) -> dict:
    return {
        "id": group.id,
        "name": group.name,
        "user_ids": [u.id for u in group.users],
    }


def extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authenticatie vereist")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Gebruik Bearer token")
    return parts[1].strip()


def get_current_user(db: Session, authorization: str | None) -> User:
    token = extract_bearer_token(authorization)
    session_token = db.query(SessionToken).filter(SessionToken.token == token).first()
    if not session_token:
        raise HTTPException(status_code=401, detail="Ongeldige sessie")
    if getattr(session_token, "expires_at", None) is not None:
        if session_token.expires_at <= datetime.utcnow():
            try:
                db.delete(session_token)
                db.commit()
            except Exception:
                db.rollback()
            raise HTTPException(status_code=401, detail="Sessie is verlopen")
    user = db.query(User).filter(User.id == session_token.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Gebruiker niet gevonden")
    session_tenant = str(getattr(session_token, "tenant_id", "") or "").strip()
    user_tenant = str(getattr(user, "tenant_id", "") or "").strip()
    if not user.is_bootstrap_admin and session_tenant and user_tenant and session_tenant != user_tenant:
        raise HTTPException(status_code=401, detail="Ongeldige sessie")
    user.active_tenant_id = session_tenant or user_tenant
    user.session_token_id = getattr(session_token, "id", None)
    user.session_token_value = getattr(session_token, "token", None)
    return user


def current_user_dependency(db: Session, authorization: str | None = Header(default=None)) -> User:
    return get_current_user(db, authorization)


def require_bootstrap_admin(user: User) -> None:
    if not user.is_bootstrap_admin:
        raise HTTPException(status_code=403, detail="Alleen bootstrap admin heeft toegang")


def require_admin_access(user: User) -> None:
    if not user_is_admin(user):
        raise HTTPException(status_code=403, detail="Alleen administrators hebben toegang")
