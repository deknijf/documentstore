import json
from datetime import datetime


def _sanitize_details(obj):
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, list):
        return [_sanitize_details(x) for x in obj][:200]
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            key = str(k)
            low = key.lower()
            if any(x in low for x in ["password", "secret", "api_key", "token", "bearer"]):
                out[key] = "***"
            else:
                out[key] = _sanitize_details(v)
        return out
    return str(obj)


def audit_log(db, *, tenant_id: str, user_id: str | None, action: str, entity_type: str, entity_id: str | None = None, details: dict | None = None, ip: str | None = None, user_agent: str | None = None):
    # Import inside function to avoid import cycles.
    from app.models import AuditLog

    payload = _sanitize_details(details or {})
    details_json = None
    if payload:
        details_json = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    row = AuditLog(
        tenant_id=str(tenant_id),
        user_id=str(user_id) if user_id else None,
        action=str(action or "").strip()[:80],
        entity_type=str(entity_type or "").strip()[:60],
        entity_id=str(entity_id)[:255] if entity_id else None,
        ip=str(ip)[:64] if ip else None,
        user_agent=str(user_agent)[:255] if user_agent else None,
        details_json=details_json,
        created_at=datetime.utcnow(),
    )
    db.add(row)
    # caller controls commit
    return row

