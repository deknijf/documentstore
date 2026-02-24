import io
from pathlib import Path

from PIL import Image, ImageOps

from app.services.image_orientation import orientation_score


def _auto_crop_document(image: Image.Image) -> Image.Image:
    """Crop photo-like documents to the detected paper area."""
    img = image.convert("RGB")
    w, h = img.size
    if w < 300 or h < 300:
        return img

    max_dim = 1400
    scale = max(w, h) / max_dim if max(w, h) > max_dim else 1.0
    sw = max(1, int(w / scale))
    sh = max(1, int(h / scale))
    small = img.resize((sw, sh), Image.Resampling.BILINEAR).convert("L")
    small = ImageOps.autocontrast(small)

    pix = list(small.getdata())
    if not pix:
        return img

    sorted_pix = sorted(pix)
    p70 = sorted_pix[int(len(sorted_pix) * 0.70)]
    p85 = sorted_pix[int(len(sorted_pix) * 0.85)]
    threshold = max(170, int((p70 + p85) / 2))

    rows = [0] * sh
    cols = [0] * sw
    bright = 0
    for y in range(sh):
        off = y * sw
        for x in range(sw):
            if pix[off + x] >= threshold:
                rows[y] += 1
                cols[x] += 1
                bright += 1

    if bright < (sw * sh * 0.12):
        return img

    row_ratio_min = 0.18
    col_ratio_min = 0.18
    valid_rows = [i for i, c in enumerate(rows) if (c / max(1, sw)) >= row_ratio_min]
    valid_cols = [i for i, c in enumerate(cols) if (c / max(1, sh)) >= col_ratio_min]
    if not valid_rows or not valid_cols:
        return img

    top, bottom = min(valid_rows), max(valid_rows)
    left, right = min(valid_cols), max(valid_cols)
    bw = right - left + 1
    bh = bottom - top + 1
    if bw < (sw * 0.35) or bh < (sh * 0.35):
        return img

    pad_x = max(8, int(bw * 0.03))
    pad_y = max(8, int(bh * 0.03))
    ox1 = max(0, int((left - pad_x) * scale))
    oy1 = max(0, int((top - pad_y) * scale))
    ox2 = min(w, int((right + pad_x) * scale))
    oy2 = min(h, int((bottom + pad_y) * scale))
    if ox2 <= ox1 or oy2 <= oy1:
        return img

    cropped = img.crop((ox1, oy1, ox2, oy2))
    cw, ch = cropped.size
    if cw < (w * 0.35) or ch < (h * 0.35):
        return img
    return cropped



def is_convertible_image_content_type(content_type: str | None) -> bool:
    return str(content_type or "").lower() in {
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/webp",
        "image/tiff",
    }


def convert_image_bytes_to_pdf(data: bytes) -> bytes:
    frames: list[Image.Image] = []
    with Image.open(io.BytesIO(data)) as src:
        frame_count = max(1, int(getattr(src, "n_frames", 1)))
        for idx in range(frame_count):
            try:
                src.seek(idx)
            except Exception:
                if idx == 0:
                    raise
                break
            # Keep upload conversion conservative:
            # 1) apply EXIF orientation
            # 2) only auto-correct 90/270 for clear landscape scans
            #    (never force 180 here to avoid upside-down false positives)
            frame = ImageOps.exif_transpose(src.copy()).convert("RGB")
            if frame.width > (frame.height * 1.05):
                r90 = frame.rotate(90, expand=True)
                r270 = frame.rotate(270, expand=True)
                s90 = orientation_score(r90)
                s270 = orientation_score(r270)
                best = r90 if s90 >= s270 else r270
                if abs(s90 - s270) >= 50:
                    frame = best
            frame = _auto_crop_document(frame)
            frames.append(frame)

    if not frames:
        raise ValueError("Geen bruikbare image-frames gevonden voor PDF-conversie")

    out = io.BytesIO()
    first, rest = frames[0], frames[1:]
    first.save(out, format="PDF", save_all=bool(rest), append_images=rest)
    return out.getvalue()


def convert_image_file_to_pdf(source_path: str | Path, target_path: str | Path) -> None:
    src = Path(source_path)
    tgt = Path(target_path)
    tgt.parent.mkdir(parents=True, exist_ok=True)
    pdf_bytes = convert_image_bytes_to_pdf(src.read_bytes())
    tgt.write_bytes(pdf_bytes)
