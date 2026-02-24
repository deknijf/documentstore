from __future__ import annotations

from PIL import Image, ImageOps


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

    return band_score + (vertical_bias * 300.0)


def orientation_score(img: Image.Image) -> float:
    return _orientation_score(img)


def orient_image_upright(img: Image.Image) -> Image.Image:
    base = ImageOps.exif_transpose(img).convert("RGB")
    candidates = [
        (0, base),
        (90, base.rotate(90, expand=True)),
        (180, base.rotate(180, expand=True)),
        (270, base.rotate(270, expand=True)),
    ]
    best_angle, best_img = candidates[0]
    best_score = _orientation_score(best_img)
    for angle, cand in candidates[1:]:
        score = _orientation_score(cand)
        if score > best_score + 1e-6:
            best_angle, best_img, best_score = angle, cand, score

    # If score gain is too small, keep original orientation to avoid over-rotation.
    if best_angle != 0 and abs(best_score - _orientation_score(base)) < 60.0:
        return base
    return best_img
