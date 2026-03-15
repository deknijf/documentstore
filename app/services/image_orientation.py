from __future__ import annotations

import re

from PIL import Image, ImageOps

try:
    import pytesseract  # type: ignore
except Exception:  # pragma: no cover - optional dependency/runtime binary
    pytesseract = None


def _osd_rotation(image: Image.Image) -> tuple[int, float] | None:
    """
    Try Tesseract OSD-based orientation detection.
    Returns (rotate_degrees_clockwise, confidence) or None.
    """
    if pytesseract is None:
        return None
    try:
        osd_text = str(
            pytesseract.image_to_osd(
                image,
                config="--psm 0",
            )
        )
    except Exception:
        return None
    m_rotate = re.search(r"Rotate:\s*([0-9]+)", osd_text)
    m_conf = re.search(r"Orientation confidence:\s*([0-9]+(?:\\.[0-9]+)?)", osd_text)
    if not m_rotate:
        return None
    try:
        angle = int(m_rotate.group(1)) % 360
    except Exception:
        return None
    try:
        conf = float(m_conf.group(1)) if m_conf else 0.0
    except Exception:
        conf = 0.0
    return angle, conf


def _variance(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / len(values)


def _orientation_score(img: Image.Image) -> float:
    # Work on a small grayscale version to keep scoring fast.
    g = ImageOps.grayscale(img)
    max_dim = 900
    w, h = g.size
    scale = max(w, h) / max_dim if max(w, h) > max_dim else 1.0
    if scale > 1:
        g = g.resize((max(1, int(w / scale)), max(1, int(h / scale))), Image.Resampling.BILINEAR)

    data = list(g.getdata())
    if not data:
        return 0.0
    thr = sum(data) / len(data)
    w, h = g.size

    row_sums = [0.0] * h
    col_sums = [0.0] * w
    for y in range(h):
        row_off = y * w
        for x in range(w):
            val = data[row_off + x]
            ink = 1.0 if val < thr else 0.0
            row_sums[y] += ink
            col_sums[x] += ink

    # Horizontal text creates stronger banding in rows than in columns.
    band_score = _variance(row_sums) - (_variance(col_sums) * 0.35)

    # Distinguish 0° vs 180° by preferring layouts with slightly more ink in the top third.
    # This helps for invoices/letters where headers usually appear near the top.
    total_ink = sum(row_sums) or 1.0
    top_ink = sum(row_sums[: max(1, h // 3)])
    bottom_ink = sum(row_sums[h - max(1, h // 3) :])
    vertical_bias = (top_ink - bottom_ink) / total_ink

    # Documents are predominantly portrait; prefer portrait unless
    # the evidence for landscape is clearly stronger.
    shape_bias = 90.0 if h >= w else -90.0

    return band_score + (vertical_bias * 300.0) + shape_bias


def orientation_score(img: Image.Image) -> float:
    return _orientation_score(img)


def orient_image_upright(img: Image.Image) -> Image.Image:
    base = ImageOps.exif_transpose(img).convert("RGB")
    # Primary orientation (paperless-like approach): OCR engine OSD.
    osd = _osd_rotation(base)
    if osd is not None:
        angle, conf = osd
        # Keep a modest threshold: good enough for rotated scans,
        # low enough to still catch difficult camera photos.
        if angle in {90, 180, 270} and conf >= 5.0:
            return base.rotate(angle, expand=True)

    # Practical guardrail from production feedback:
    # avoid automatic 180° flips because they produce too many false positives
    # on photographed documents with folds/shadows. Keep 90°/270° auto-fix.
    candidates = [
        (0, base),
        (90, base.rotate(90, expand=True)),
        (270, base.rotate(270, expand=True)),
    ]
    best_angle, best_img = candidates[0]
    best_score = _orientation_score(best_img)
    for angle, cand in candidates[1:]:
        score = _orientation_score(cand)
        if score > best_score + 1e-6:
            best_angle, best_img, best_score = angle, cand, score

    # Heuristic fallback: be conservative to avoid false 180 flips.
    base_score = _orientation_score(base)
    scored = sorted([_orientation_score(c) for _, c in candidates], reverse=True)
    second_score = scored[1] if len(scored) > 1 else base_score
    gain = abs(best_score - base_score)
    sep = abs(best_score - second_score)
    min_gain = 80.0
    min_sep = 25.0
    if best_angle != 0 and (gain < min_gain or sep < min_sep):
        return base
    return best_img
