import io
from pathlib import Path

import fitz
from PIL import Image, ImageOps

from app.config import settings
from app.services.image_orientation import orientation_score, orient_image_upright

try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - runtime fallback when opencv is unavailable
    cv2 = None
    np = None


def _opencv_available() -> bool:
    return bool(cv2 is not None and np is not None)


def _resize_for_output(img: Image.Image) -> Image.Image:
    max_dim = max(1200, int(settings.doc_preprocess_output_max_dim or 2400))
    w, h = img.size
    longest = max(w, h)
    if longest <= max_dim:
        return img
    scale = max_dim / float(longest)
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    return img.resize((nw, nh), Image.Resampling.LANCZOS)


def _frames_to_pdf_bytes(frames: list[Image.Image]) -> bytes:
    if not frames:
        raise ValueError("Geen frames beschikbaar voor PDF-opbouw")
    quality = int(settings.doc_preprocess_output_jpeg_quality or 82)
    quality = min(95, max(55, quality))

    doc = fitz.open()
    try:
        for frame in frames:
            page_img = _resize_for_output(frame.convert("RGB"))
            jpg_io = io.BytesIO()
            page_img.save(
                jpg_io,
                format="JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
                subsampling=1,
            )
            jpg = jpg_io.getvalue()
            img_doc = fitz.open(stream=jpg, filetype="jpeg")
            rect = img_doc[0].rect
            page = doc.new_page(width=rect.width, height=rect.height)
            page.insert_image(rect, stream=jpg)
            img_doc.close()
        return doc.write(deflate=True, garbage=3, clean=True)
    finally:
        doc.close()


def _order_quad_points(points):
    pts = np.array(points, dtype="float32")
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]
    tr = pts[np.argmin(diff)]
    bl = pts[np.argmax(diff)]
    return np.array([tl, tr, br, bl], dtype="float32")


def _perspective_transform(img_rgb: Image.Image) -> Image.Image:
    if not _opencv_available() or not settings.doc_preprocess_perspective_enabled:
        return img_rgb
    arr = np.array(img_rgb.convert("RGB"))
    h, w = arr.shape[:2]
    if w < 300 or h < 300:
        return img_rgb

    max_dim = 1600
    scale = max(h, w) / float(max_dim) if max(h, w) > max_dim else 1.0
    sw = max(1, int(w / scale))
    sh = max(1, int(h / scale))
    small = cv2.resize(arr, (sw, sh), interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 45, 140)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:15] if contours else []
    img_area = float(sw * sh)
    best_quad = None
    best_area = 0.0
    for c in contours:
        area = float(cv2.contourArea(c))
        if area < (img_area * 0.18):
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) != 4:
            continue
        if area > best_area:
            best_area = area
            best_quad = approx.reshape(4, 2)
    if best_quad is None:
        # Fallback for folded/low-contrast pages: detect a bright page region first.
        _, bright = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        if np.mean(bright) < 120:
            bright = cv2.bitwise_not(bright)
        bright = cv2.morphologyEx(bright, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8), iterations=2)
        cnt2, _ = cv2.findContours(bright, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if cnt2:
            c = max(cnt2, key=cv2.contourArea)
            area = float(cv2.contourArea(c))
            if area > (img_area * 0.22):
                rect = cv2.minAreaRect(c)
                box = cv2.boxPoints(rect)
                best_quad = box.reshape(4, 2)
    if best_quad is None:
        return img_rgb

    quad = _order_quad_points(best_quad * scale)
    tl, tr, br, bl = quad
    width_a = np.linalg.norm(br - bl)
    width_b = np.linalg.norm(tr - tl)
    height_a = np.linalg.norm(tr - br)
    height_b = np.linalg.norm(tl - bl)
    max_w = int(max(width_a, width_b))
    max_h = int(max(height_a, height_b))
    if max_w < (w * 0.35) or max_h < (h * 0.35):
        return img_rgb

    dst = np.array(
        [[0, 0], [max_w - 1, 0], [max_w - 1, max_h - 1], [0, max_h - 1]],
        dtype="float32",
    )
    M = cv2.getPerspectiveTransform(quad, dst)
    warped = cv2.warpPerspective(arr, M, (max_w, max_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return Image.fromarray(warped)


def _deskew_image(img_rgb: Image.Image) -> Image.Image:
    if not _opencv_available() or not settings.doc_preprocess_deskew_enabled:
        return img_rgb
    arr = np.array(img_rgb.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    angle = 0.0
    angle = _estimate_line_skew_angle(th)
    if angle is not None:
        angle = -float(angle)
    else:
        coords = np.column_stack(np.where(th > 0))
        if coords.size == 0:
            return img_rgb
        rect = cv2.minAreaRect(coords)
        raw = float(rect[-1])
        if raw < -45:
            angle = -(90 + raw)
        else:
            angle = -raw
    if abs(angle) < 0.3 or abs(angle) > 15:
        return img_rgb

    rotated = _rotate_array(arr, angle)
    return Image.fromarray(rotated)


def _estimate_line_skew_angle(binary_inv: "np.ndarray") -> float | None:
    lines = cv2.HoughLinesP(
        binary_inv,
        rho=1,
        theta=np.pi / 180.0,
        threshold=80,
        minLineLength=max(80, int(min(binary_inv.shape[:2]) * 0.12)),
        maxLineGap=12,
    )
    line_angles: list[float] = []
    if lines is not None:
        for line in lines[:, 0]:
            x1, y1, x2, y2 = map(float, line)
            dx, dy = (x2 - x1), (y2 - y1)
            length = (dx * dx + dy * dy) ** 0.5
            if length < 40:
                continue
            a = np.degrees(np.arctan2(dy, dx))
            while a <= -45:
                a += 90
            while a > 45:
                a -= 90
            if abs(a) <= 25:
                line_angles.append(a)
    if not line_angles:
        return None
    return float(np.median(line_angles))


def _rotate_array(arr: "np.ndarray", angle: float) -> "np.ndarray":
    h, w = arr.shape[:2]
    center = (w / 2, h / 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(arr, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def _fine_deskew_image(img_rgb: Image.Image) -> Image.Image:
    if not _opencv_available() or not settings.doc_preprocess_deskew_enabled:
        return img_rgb
    arr = np.array(img_rgb.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    angle = _estimate_line_skew_angle(th)
    if angle is None:
        return img_rgb
    corr = -float(angle)
    # Allow larger fine correction for camera photos; small cap avoids over-rotation.
    if abs(corr) < 0.2 or abs(corr) > 15:
        return img_rgb
    # Use expand=True with white fill to avoid clipping top/bottom text lines.
    return img_rgb.rotate(corr, expand=True, fillcolor=(255, 255, 255))


def _trim_document_margins(img_rgb: Image.Image) -> Image.Image:
    if not _opencv_available():
        return img_rgb
    arr = np.array(img_rgb.convert("RGB"))
    h, w = arr.shape[:2]
    if w < 300 or h < 300:
        return img_rgb
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    # Keep non-background content; robust for light documents on dark backgrounds.
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=1)
    coords = cv2.findNonZero(mask)
    if coords is None:
        return img_rgb
    x, y, bw, bh = cv2.boundingRect(coords)
    if bw < (w * 0.4) or bh < (h * 0.4):
        return img_rgb
    pad_x = max(10, int(bw * 0.02))
    pad_y = max(10, int(bh * 0.02))
    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x2 = min(w, x + bw + pad_x)
    y2 = min(h, y + bh + pad_y)
    if x2 <= x1 or y2 <= y1:
        return img_rgb
    cropped = arr[y1:y2, x1:x2]
    return Image.fromarray(cropped)


def _auto_upright_orientation(img_rgb: Image.Image) -> Image.Image:
    # Centralized orientation logic (OSD first, conservative heuristic fallback).
    return orient_image_upright(img_rgb)


def _enhance_document_image(img_rgb: Image.Image) -> Image.Image:
    if not _opencv_available() or not settings.doc_preprocess_enhance_enabled:
        return img_rgb
    arr = np.array(img_rgb.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    # Background normalization to reduce shadows/folds impact.
    dilated = cv2.dilate(gray, np.ones((7, 7), np.uint8))
    bg = cv2.medianBlur(dilated, 21)
    diff = 255 - cv2.absdiff(gray, bg)
    norm = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)

    clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
    enhanced = clahe.apply(norm)
    out = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
    # Keep enhancement readable but less aggressive:
    # blend with original to preserve thin text/details (e.g. headers).
    blended = cv2.addWeighted(arr, 0.68, out, 0.32, 0)
    return Image.fromarray(blended)


def _opencv_scan_pipeline(img_rgb: Image.Image) -> Image.Image:
    if not settings.doc_preprocess_opencv_enabled:
        return img_rgb
    if not _opencv_available():
        return img_rgb
    out = _perspective_transform(img_rgb)
    out = _deskew_image(out)
    out = _enhance_document_image(out)
    return out


def _is_aggressive_transform(base: Image.Image, out: Image.Image) -> bool:
    """
    Guardrail: reject transforms that likely cut document content.
    """
    bw, bh = base.size
    ow, oh = out.size
    if bw <= 0 or bh <= 0 or ow <= 0 or oh <= 0:
        return True
    base_area = float(bw * bh)
    out_area = float(ow * oh)
    if out_area < (base_area * 0.45):
        return True
    if ow < (bw * 0.55) or oh < (bh * 0.55):
        return True
    base_ratio = bw / float(bh)
    out_ratio = ow / float(oh)
    if base_ratio > 0 and out_ratio > 0:
        rel_diff = abs(out_ratio - base_ratio) / base_ratio
        if rel_diff > 0.55:
            return True
    return False


def _safe_scan_pipeline(img_rgb: Image.Image) -> Image.Image:
    out = _opencv_scan_pipeline(img_rgb)
    if _is_aggressive_transform(img_rgb, out):
        return img_rgb
    return out


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

    # Keep crop conservative: we prefer a little background over cutting real document lines.
    pad_x = max(24, int(bw * 0.08))
    pad_y = max(32, int(bh * 0.10))
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
            frame = _safe_scan_pipeline(frame)
            frame = _auto_crop_document(frame)
            frame = _auto_upright_orientation(frame)
            frame = _fine_deskew_image(frame)
            frames.append(frame)

    if not frames:
        raise ValueError("Geen bruikbare image-frames gevonden voor PDF-conversie")

    return _frames_to_pdf_bytes(frames)


def convert_image_file_to_pdf(source_path: str | Path, target_path: str | Path) -> None:
    src = Path(source_path)
    tgt = Path(target_path)
    tgt.parent.mkdir(parents=True, exist_ok=True)
    pdf_bytes = convert_image_bytes_to_pdf(src.read_bytes())
    tgt.write_bytes(pdf_bytes)


def convert_pdf_file_to_optimized_pdf(source_path: str | Path, target_path: str | Path) -> None:
    src = Path(source_path)
    tgt = Path(target_path)
    tgt.parent.mkdir(parents=True, exist_ok=True)

    frames: list[Image.Image] = []
    with fitz.open(str(src)) as pdf:
        for page in pdf:
            base_w = float(page.rect.width or 1.0)
            base_h = float(page.rect.height or 1.0)
            max_dim = float(max(1200, int(settings.doc_preprocess_output_max_dim or 2400)))
            zoom = max(1.0, min(3.0, max_dim / max(base_w, base_h)))
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            frame = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            frame = _safe_scan_pipeline(frame)
            # Keep full page for PDF sources; cropping here can remove
            # header/footer text on photographed scans embedded as PDF.
            frame = _auto_upright_orientation(frame)
            frame = _fine_deskew_image(frame)
            frames.append(frame.convert("RGB"))

    if not frames:
        raise ValueError("Geen bruikbare PDF-pagina's gevonden voor preprocess")

    tgt.write_bytes(_frames_to_pdf_bytes(frames))
