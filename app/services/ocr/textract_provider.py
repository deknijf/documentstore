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

    def _pdf_pages_to_upright_png(self, file_path: str, max_pages: int = 8) -> list[bytes]:
        doc = fitz.open(file_path)
        out: list[bytes] = []
        for i in range(min(doc.page_count, max_pages)):
            pix = doc.load_page(i).get_pixmap(matrix=fitz.Matrix(2, 2))
            with Image.open(BytesIO(pix.tobytes("png"))) as raw:
                upright = orient_image_upright(raw)
                buf = BytesIO()
                upright.save(buf, format="PNG")
                out.append(buf.getvalue())
        doc.close()
        return out

    def _image_to_upright_png(self, file_path: str) -> bytes:
        with Image.open(file_path) as raw:
            upright = orient_image_upright(raw)
            buf = BytesIO()
            upright.save(buf, format="PNG")
            return buf.getvalue()

    def extract_text(self, file_path: str, content_type: str) -> str:
        if content_type == "application/pdf":
            pages = self._pdf_pages_to_upright_png(file_path)
            page_text = [self._extract_from_image_bytes(p) for p in pages]
            return "\n\n".join([t for t in page_text if t.strip()])

        data = self._image_to_upright_png(file_path)
        return self._extract_from_image_bytes(data)
