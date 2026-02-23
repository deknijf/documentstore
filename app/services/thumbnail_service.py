import io
from pathlib import Path

import fitz
from PIL import Image, ImageOps


class ThumbnailService:
    def create_thumbnail(self, file_path: str, content_type: str, output_path: str) -> str:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        if content_type == "application/pdf":
            self._pdf_thumbnail(file_path, output_path)
        else:
            self._image_thumbnail(file_path, output_path)
        return output_path

    def _pdf_thumbnail(self, file_path: str, output_path: str) -> None:
        doc = fitz.open(file_path)
        pix = doc.load_page(0).get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        doc.close()
        img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        img = self._normalize_thumbnail_orientation(img)
        img.thumbnail((480, 480))
        img.save(output_path, format="JPEG", quality=85)

    def _image_thumbnail(self, file_path: str, output_path: str) -> None:
        with Image.open(file_path) as img:
            out = self._normalize_thumbnail_orientation(img)
            out.thumbnail((480, 480))
            out.save(output_path, format="JPEG", quality=85)

    def _normalize_thumbnail_orientation(self, img: Image.Image) -> Image.Image:
        # Keep thumbnail orientation aligned with document-detail viewer:
        # apply EXIF orientation only, no heuristic rotation.
        return ImageOps.exif_transpose(img).convert("RGB")
