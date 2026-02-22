import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.legacy_main import get_current_user_dep, get_db
from app.models import SavedView, User
from app.schemas import CreateSavedViewIn, SavedViewOut
from app.services.audit import audit_log

router = APIRouter(prefix="/api/views", tags=["views"])


@router.get("", response_model=list[SavedViewOut])
def list_views(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_dep)):
    items = (
        db.query(SavedView)
        .filter(SavedView.tenant_id == current_user.tenant_id, SavedView.user_id == current_user.id)
        .order_by(SavedView.updated_at.desc())
        .all()
    )
    out: list[SavedViewOut] = []
    for v in items:
        try:
            filters = json.loads(v.filters_json or "{}")
        except Exception:
            filters = {}
        out.append(
            SavedViewOut(
                id=v.id,
                name=v.name,
                filters=filters if isinstance(filters, dict) else {},
                created_at=v.created_at,
                updated_at=v.updated_at,
            )
        )
    return out


@router.post("", response_model=SavedViewOut)
def create_or_update_view(
    body: CreateSavedViewIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    name = (body.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Naam is verplicht.")
    if len(name) > 120:
        raise HTTPException(status_code=400, detail="Naam is te lang.")
    if not isinstance(body.filters, dict) or not body.filters:
        raise HTTPException(status_code=400, detail="Filters zijn verplicht (minstens 1 filter).")

    filters_json = json.dumps(body.filters, ensure_ascii=True, separators=(",", ":"))
    existing = (
        db.query(SavedView)
        .filter(
            SavedView.tenant_id == current_user.tenant_id,
            SavedView.user_id == current_user.id,
            SavedView.name == name,
        )
        .first()
    )
    if existing:
        existing.filters_json = filters_json
        db.commit()
        db.refresh(existing)
        try:
            audit_log(
                db,
                tenant_id=current_user.tenant_id,
                user_id=str(current_user.id),
                action="views.update",
                entity_type="saved_view",
                entity_id=str(existing.id),
                details={"name": name},
            )
            db.commit()
        except Exception:
            db.rollback()
        return SavedViewOut(
            id=existing.id,
            name=existing.name,
            filters=body.filters,
            created_at=existing.created_at,
            updated_at=existing.updated_at,
        )

    item = SavedView(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        name=name,
        filters_json=filters_json,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    try:
        audit_log(
            db,
            tenant_id=current_user.tenant_id,
            user_id=str(current_user.id),
            action="views.create",
            entity_type="saved_view",
            entity_id=str(item.id),
            details={"name": name},
        )
        db.commit()
    except Exception:
        db.rollback()
    return SavedViewOut(
        id=item.id,
        name=item.name,
        filters=body.filters,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.delete("/{view_id}")
def delete_view(view_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_dep)):
    item = (
        db.query(SavedView)
        .filter(
            SavedView.tenant_id == current_user.tenant_id,
            SavedView.user_id == current_user.id,
            SavedView.id == view_id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="View niet gevonden.")
    db.delete(item)
    db.commit()
    try:
        audit_log(
            db,
            tenant_id=current_user.tenant_id,
            user_id=str(current_user.id),
            action="views.delete",
            entity_type="saved_view",
            entity_id=str(view_id),
            details={"name": str(item.name or "")},
        )
        db.commit()
    except Exception:
        db.rollback()
    return {"ok": True}
