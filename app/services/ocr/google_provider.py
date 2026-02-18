import base64
import io

import fitz
import requests
from PIL import Image

from app.config import settings
from app.services.image_orientation import orient_image_upright
from app.services.ocr.base import OCRProvider


class GoogleOCRProvider(OCRProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.google_api_key
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY ontbreekt")
        self.model = model or settings.google_ocr_model
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def _render_pdf(self, file_path: str, max_pages: int = 3) -> list[bytes]:
        doc = fitz.open(file_path)
        images: list[bytes] = []
        for i in range(min(doc.page_count, max_pages)):
            pix = doc.load_page(i).get_pixmap(matrix=fitz.Matrix(2, 2))
            with Image.open(io.BytesIO(pix.tobytes("png"))) as raw:
                upright = orient_image_upright(raw)
                buf = io.BytesIO()
                upright.save(buf, format="PNG")
                images.append(buf.getvalue())
        doc.close()
        return images

    def _prepare_images(self, file_path: str, content_type: str) -> list[bytes]:
        if content_type == "application/pdf":
            return self._render_pdf(file_path)
        with Image.open(file_path) as img:
            buf = io.BytesIO()
            upright = orient_image_upright(img)
            upright.save(buf, format="PNG")
            return [buf.getvalue()]

    def extract_text(self, file_path: str, content_type: str) -> str:
        images = self._prepare_images(file_path, content_type)
        parts: list[dict] = [
            {"text": "Transcribeer het document exact. Geef alleen de tekst, zonder uitleg."}
        ]
        for img in images:
            parts.append(
                {
                    "inlineData": {
                        "mimeType": "image/png",
                        "data": base64.b64encode(img).decode("utf-8"),
                    }
                }
            )

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {"temperature": 0},
        }
        response = requests.post(
            self.base_url,
            params={"key": self.api_key},
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        return str(text or "").strip()

