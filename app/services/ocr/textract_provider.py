from io import BytesIO

import boto3
import fitz
from PIL import Image

from app.config import settings
from app.services.image_orientation import orient_image_upright
from app.services.ocr.base import OCRProvider


class TextractOCRProvider(OCRProvider):
    def __init__(self, region: str | None = None, access_key: str | None = None, secret_key: str | None = None) -> None:
        kwargs: dict[str, str] = {"region_name": region or settings.aws_region}
        resolved_access_key = access_key or settings.aws_access_key_id
        resolved_secret_key = secret_key or settings.aws_secret_access_key
        if resolved_access_key and resolved_secret_key:
            kwargs["aws_access_key_id"] = resolved_access_key
            kwargs["aws_secret_access_key"] = resolved_secret_key
        self.client = boto3.client("textract", **kwargs)

    def _extract_from_image_bytes(self, image_bytes: bytes) -> str:
        response = self.client.detect_document_text(Document={"Bytes": image_bytes})
        lines = [b.get("Text", "") for b in response.get("Blocks", []) if b.get("BlockType") == "LINE"]
        return "\n".join(filter(None, lines))

    def _render_page_upright_bytes(self, page: fitz.Page) -> bytes:
        # Keep OCR raster under practical Textract limits:
        # - avoid huge PNG payloads from large phone-photo PDFs
        # - keep enough detail for OCR quality
        rect = page.rect
        w = max(1.0, float(rect.width))
        h = max(1.0, float(rect.height))
        max_pixels = 7_000_000.0
        base_scale = 2.0
        scale = min(base_scale, (max_pixels / (w * h)) ** 0.5)
        scale = max(0.35, scale)
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
        with Image.open(BytesIO(pix.tobytes("png"))) as raw:
            upright = orient_image_upright(raw).convert("RGB")
            # JPEG keeps request payload small and avoids Textract invalid-params on oversized bytes.
            buf = BytesIO()
            upright.save(buf, format="JPEG", quality=88, optimize=True)
            return buf.getvalue()

    def _pdf_pages_to_upright_bytes(self, file_path: str, max_pages: int = 8) -> list[bytes]:
        doc = fitz.open(file_path)
        out: list[bytes] = []
        for i in range(min(doc.page_count, max_pages)):
            out.append(self._render_page_upright_bytes(doc.load_page(i)))
        doc.close()
        return out

    def _image_to_upright_bytes(self, file_path: str) -> bytes:
        with Image.open(file_path) as raw:
            upright = orient_image_upright(raw).convert("RGB")
            # Bound image size to avoid oversized request bytes.
            max_dim = 3500
            if max(upright.size) > max_dim:
                ratio = max_dim / float(max(upright.size))
                upright = upright.resize(
                    (max(1, int(upright.width * ratio)), max(1, int(upright.height * ratio))),
                    Image.Resampling.BILINEAR,
                )
            buf = BytesIO()
            upright.save(buf, format="JPEG", quality=88, optimize=True)
            return buf.getvalue()

    def extract_text(self, file_path: str, content_type: str) -> str:
        if content_type == "application/pdf":
            pages = self._pdf_pages_to_upright_bytes(file_path)
            page_text = [self._extract_from_image_bytes(p) for p in pages]
            return "\n\n".join([t for t in page_text if t.strip()])

        data = self._image_to_upright_bytes(file_path)
        return self._extract_from_image_bytes(data)
