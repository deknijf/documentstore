from pathlib import Path

from app.config import settings


def ensure_dirs() -> None:
    Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.preprocessed_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.thumbnails_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.avatars_dir).mkdir(parents=True, exist_ok=True)


def allowed_content_type(content_type: str) -> bool:
    return content_type in {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/webp",
        "image/tiff",
    }


_MAGIC_PREFIXES = (
    (b"%PDF-", "application/pdf"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"II*\x00", "image/tiff"),
    (b"MM\x00*", "image/tiff"),
)

_EXTENSION_BY_CONTENT_TYPE = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
    "image/tiff": ".tif",
}


def sniff_content_type(data: bytes) -> str | None:
    """Detect the real content type from the file's own bytes.

    The multipart Content-Type is client-supplied, so it must not decide the
    storage extension or which processing branch runs.
    """
    head = bytes(data or b"")[:1024]
    if not head:
        return None
    for prefix, content_type in _MAGIC_PREFIXES:
        if head.startswith(prefix):
            return content_type
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    # Some scanners emit a short preamble before the PDF header.
    if b"%PDF-" in head:
        return "application/pdf"
    return None


def extension_for_content_type(content_type: str) -> str:
    return _EXTENSION_BY_CONTENT_TYPE.get(str(content_type or "").strip().lower(), ".bin")


def allowed_avatar_content_type(content_type: str) -> bool:
    return content_type in {
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/webp",
    }
