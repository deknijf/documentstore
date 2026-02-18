import base64
import io

import fitz
import requests
from PIL import Image

from app.config import settings
from app.services.image_orientation import orient_image_upright
from app.services.ocr.base import OCRProvider


class OpenRouterOCRProvider(OCRProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.openrouter_api_key
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY ontbreekt")
        self.model = model or settings.openrouter_ocr_model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def _img_to_data_uri(self, data: bytes, mime: str = "image/png") -> str:
        b64 = base64.b64encode(data).decode("utf-8")
        return f"data:{mime};base64,{b64}"

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
        content_blocks: list[dict] = [
            {
                "type": "text",
                "text": "Transcribeer het document exact. Geef alleen de tekst, zonder uitleg.",
            }
        ]
        for img_bytes in images:
            content_blocks.append(
                {
                    "type": "image_url",
                    "image_url": {"url": self._img_to_data_uri(img_bytes)},
                }
            )

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": content_blocks}],
            "temperature": 0,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(self.base_url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
