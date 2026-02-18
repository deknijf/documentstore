from pathlib import Path

from app.config import settings


def ensure_dirs() -> None:
    Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
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


def allowed_avatar_content_type(content_type: str) -> bool:
    return content_type in {
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/webp",
    }
