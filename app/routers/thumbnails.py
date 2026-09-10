from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.legacy_main import get_db
from app.models import Document
from app.services.file_tokens import SCOPE_THUMBNAIL, verify

router = APIRouter()


@router.get("/thumbnails/{thumbnail_name}")
def get_thumbnail(
    thumbnail_name: str,
    exp: str | None = Query(default=None),
    sig: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> FileResponse:
    # Thumbnails are rendered by <img>, which cannot send an Authorization
    # header, so access is proven by the signed URL the API handed out.
    name = Path(str(thumbnail_name or "")).name
    document_id = Path(name).stem
    if not name or not document_id:
        raise HTTPException(status_code=404, detail="Niet gevonden")
    if not verify(SCOPE_THUMBNAIL, document_id, "", exp, sig):
        raise HTTPException(status_code=404, detail="Niet gevonden")

    # Deleted documents keep their thumbnail: the trash view still renders cards
    # for them. The thumbnail file itself is removed by the purge job.
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Niet gevonden")

    path = Path(settings.thumbnails_dir) / name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Niet gevonden")
    return FileResponse(
        path,
        media_type="image/jpeg",
        headers={"Cache-Control": "private, max-age=3600"},
    )
