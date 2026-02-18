import io
from pathlib import Path

import fitz
from PIL import Image, ImageOps

from app.services.image_orientation import orientation_score


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
        base = ImageOps.exif_transpose(img).convert("RGB")
        candidates = [
            base,
            base.rotate(90, expand=True),
            base.rotate(180, expand=True),
            base.rotate(270, expand=True),
        ]

        def upper_ink_bias(cand: Image.Image) -> float:
            # Prefer orientation where "ink" is slightly more present in the upper half.
            g = ImageOps.grayscale(cand)
            w, h = g.size
            if w <= 0 or h <= 1:
                return 0.0
            max_dim = 700
            scale = max(w, h) / max_dim if max(w, h) > max_dim else 1.0
            if scale > 1:
                g = g.resize((max(1, int(w / scale)), max(2, int(h / scale))), Image.Resampling.BILINEAR)
                w, h = g.size

            data = list(g.getdata())
            if not data:
                return 0.0
            thr = sum(data) / len(data)
            mid = h // 2
            top_ink = 0.0
            bottom_ink = 0.0
            for y in range(h):
                row_off = y * w
                row_ink = 0.0
                for x in range(w):
                    row_ink += 1.0 if data[row_off + x] < thr else 0.0
                if y < mid:
                    top_ink += row_ink
                else:
                    bottom_ink += row_ink
            denom = max(1.0, top_ink + bottom_ink)
            return (top_ink - bottom_ink) / denom

        def scored(cand: Image.Image) -> float:
            score = orientation_score(cand)
            # Thumbnails are expected mostly portrait for document pages.
            if cand.height > cand.width:
                score += 0.2
                ratio = cand.height / max(1, cand.width)
                score += min(0.25, max(0.0, (ratio - 1.0) * 0.25))
            score += upper_ink_bias(cand) * 0.6
            return score

        best = candidates[0]
        best_score = scored(best)
        for cand in candidates[1:]:
            s = scored(cand)
            if s > best_score:
                best = cand
                best_score = s
        return best
