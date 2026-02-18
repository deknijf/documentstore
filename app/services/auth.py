import hashlib
import hmac
import os
import uuid

from fastapi import Header, HTTPException
from sqlalchemy.orm import Session

from app.models import Group, SessionToken, User


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
    db.add(SessionToken(token=token, user_id=user.id))
    db.commit()
    return token


def user_group_ids(user: User) -> list[str]:
    return [g.id for g in user.groups]


def user_is_admin(user: User) -> bool:
    if user.is_bootstrap_admin:
        return True
    return any((g.name or "").strip().lower() == "administrators" for g in (user.groups or []))


def user_to_out(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "avatar_path": user.avatar_path,
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
    user = db.query(User).filter(User.id == session_token.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Gebruiker niet gevonden")
    return user


def current_user_dependency(db: Session, authorization: str | None = Header(default=None)) -> User:
    return get_current_user(db, authorization)


def require_bootstrap_admin(user: User) -> None:
    if not user.is_bootstrap_admin:
        raise HTTPException(status_code=403, detail="Alleen bootstrap admin heeft toegang")


def require_admin_access(user: User) -> None:
    if not user_is_admin(user):
        raise HTTPException(status_code=403, detail="Alleen administrators hebben toegang")
