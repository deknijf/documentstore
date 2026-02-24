from pathlib import Path

from app.config import settings
from app.db import SessionLocal
from app.models import Document
from app.services.document_conversion import convert_image_file_to_pdf, is_convertible_image_content_type
from app.services.thumbnail_service import ThumbnailService


def run() -> None:
    db = SessionLocal()
    converted = 0
    skipped = 0
    failed = 0
    thumb = ThumbnailService()

    try:
        docs = (
            db.query(Document)
            .filter(Document.content_type.in_(["image/png", "image/jpeg", "image/jpg", "image/webp", "image/tiff"]))
            .all()
        )
        for doc in docs:
            src = Path(str(doc.file_path or ""))
            if not src.exists():
                skipped += 1
                continue
            if not is_convertible_image_content_type(doc.content_type):
                skipped += 1
                continue
            target = Path(settings.uploads_dir) / f"{doc.id}.pdf"
            try:
                convert_image_file_to_pdf(src, target)
                doc.content_type = "application/pdf"
                doc.file_path = str(target)
                doc.filename = f"{Path(str(doc.filename or doc.id)).stem}.pdf"

                thumb_name = f"{doc.id}.jpg"
                thumb_fs_path = Path(settings.thumbnails_dir) / thumb_name
                thumb.create_thumbnail(doc.file_path, "application/pdf", str(thumb_fs_path))
                doc.thumbnail_path = f"/thumbnails/{thumb_name}"

                if src.resolve() != target.resolve():
                    src.unlink(missing_ok=True)
                converted += 1
            except Exception as exc:
                print(f"[FAIL] {doc.id}: {exc}")
                failed += 1

        db.commit()
        print(f"Converted: {converted}, Skipped: {skipped}, Failed: {failed}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
