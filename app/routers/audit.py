import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.legacy_main import get_current_user_dep, get_db, require_admin_access, _tenant_id_for_user
from app.models import AuditLog, User
from app.schemas import AuditLogOut

router = APIRouter(prefix="/api/admin/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogOut])
def list_audit_logs(
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    tenant_id = _tenant_id_for_user(current_user)
    rows = (
        db.query(AuditLog)
        .filter(AuditLog.tenant_id == tenant_id)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    user_ids = {str(r.user_id) for r in rows if r.user_id}
    users = []
    if user_ids:
        users = db.query(User).filter(User.id.in_(list(user_ids))).all()
    user_by_id = {str(u.id): u for u in users}

    out: list[AuditLogOut] = []
    for r in rows:
        u = user_by_id.get(str(r.user_id or ""))
        try:
            details = json.loads(r.details_json or "{}")
        except Exception:
            details = {}
        out.append(
            AuditLogOut(
                id=str(r.id),
                created_at=r.created_at,
                user_id=str(r.user_id) if r.user_id else None,
                user_name=str(getattr(u, "name", "") or "") if u else None,
                user_email=str(getattr(u, "email", "") or "") if u else None,
                action=str(r.action or ""),
                entity_type=str(r.entity_type or ""),
                entity_id=str(r.entity_id or "") or None,
                ip=str(r.ip or "") or None,
                user_agent=str(r.user_agent or "") or None,
                details=details if isinstance(details, dict) else {},
            )
        )
    return out

