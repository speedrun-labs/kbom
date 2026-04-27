"""Path A geometry adapter — reads vector PDFs into structured evidence.

Distills the Phase 0 work (test1_pdf_vector_check.py + identify_pages.py +
crop_views.py + render_pages.py) into a clean reusable interface.

Public entry points:
  - identify_variants(pdf_path) → list of (page, type_code, label)
  - extract_geometry(pdf_path, page) → GeometryEvidence
  - render_page(pdf_path, page, dpi) → PIL.Image

The adapter is purely deterministic (no AI). Vision/AI happens in the next
pipeline stage (kbom.vision).
"""
from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Iterator

import fitz  # pymupdf
import pdfplumber
from PIL import Image

from kbom.models import CabinetSegment, GeometryEvidence


# -----------------------------------------------------------------------------
# Variant detection (per-page dispatcher)
# -----------------------------------------------------------------------------
# Matches "26㎡ A형", "26㎡ A1형 (주거약자형)", "37㎡ B형", "46㎡ A형", etc.
# The 평/m² character can be ㎡ or m² depending on encoding.
# LH-published apartment unit sizes (square meters). Restricting prevents the
# regex from picking up unrelated digits that happen to precede a ㎡ symbol.
_KNOWN_SIZES = {"26", "29", "32", "35", "37", "45", "46", "49", "51", "59", "75", "84"}
# Match "26㎡ A형", "37㎡ A1형 (주거약자형)", etc. Allow optional whitespace.
# The known-sizes filter handles false matches (no lookbehind needed).
_VARIANT_RE = re.compile(
    r"(\d{2})\s*[㎡m²]\s*([A-Z]\d?)\s*형(?:\s*\(([^)]+)\))?"
)


def identify_variants(pdf_path: str | Path) -> list[tuple[int, str, str]]:
    """Scan PDF pages for unit-type identifiers in title blocks.

    Returns a list of (page_number_1indexed, type_code, full_label) tuples.
    Skips title-only divider pages (very low word count).

    Example: [(2, "26A", "26㎡ A형 (일반형)"), (4, "26A1", "26㎡ A1형 (주거약자형)"), ...]
    """
    results: list[tuple[int, str, str]] = []
    seen_codes: set[str] = set()

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_idx, page in enumerate(pdf.pages, start=1):
            words = page.extract_words() or []
            if len(words) < 50:  # divider/title page, not a detail page
                continue

            text = " ".join(w["text"] for w in words)
            # Don't collapse spaces — the known-sizes filter handles false matches,
            # and the dimension labels nearby (e.g. "1" section number followed by
            # "26㎡ A형") would falsely match if collapsed.

            for m in _VARIANT_RE.finditer(text):
                size, letter_num, qualifier = m.group(1), m.group(2), m.group(3)
                if size not in _KNOWN_SIZES:
                    continue
                code = f"{size}{letter_num}"  # e.g. "26A", "37B1"
                qualifier_text = f" ({qualifier})" if qualifier else ""
                label = f"{size}㎡ {letter_num}형{qualifier_text}"

                # First detail page that mentions this code wins
                if code not in seen_codes:
                    seen_codes.add(code)
                    results.append((page_idx, code, label))
                break  # one variant per page

    return results


# -----------------------------------------------------------------------------
# Per-page geometry extraction
# -----------------------------------------------------------------------------
# Heuristics for finding dimension labels — they're integers between 10 and 5000mm
# (cabinet runs rarely exceed 4-5m), often appearing in a horizontal sequence.
_DIM_RE = re.compile(r"^(\d{2,4}(?:,\d{3})?)$")
_BIG_DIM_RE = re.compile(r"^[1-5],\d{3}$")  # "2,120" total-run dimension


def extract_geometry(
    pdf_path: str | Path, page_num: int, render_dpi: int = 150
) -> GeometryEvidence:
    """Read all extractable evidence from one page.

    Populates dimension ladders, finish spec, title-block text, and pixel-accurate
    cabinet-segment positions for SVG overlay rendering. Does NOT do AI-based
    symbol classification — that's the vision stage's job.
    """
    evidence = GeometryEvidence(render_dpi=render_dpi)

    with pdfplumber.open(str(pdf_path)) as pdf:
        page = pdf.pages[page_num - 1]
        # Default tolerance for general text extraction
        words = page.extract_words() or []
        evidence.raw_text_strings = [w["text"] for w in words]
        evidence.title_block_text = " ".join(evidence.raw_text_strings)

        # Image dimensions at the target DPI (PDF page is in points, 1pt = 1/72 inch)
        scale = render_dpi / 72.0
        evidence.image_width_px = int(round(page.width * scale))
        evidence.image_height_px = int(round(page.height * scale))

        # Stricter tolerance for dimension labels — LH dimension labels often sit
        # very close to each other (e.g. "20" + "280" with <1pt gap), and
        # the default tolerance (3pt) merges them into "20280".
        dim_words = page.extract_words(x_tolerance=0.5) or []

        # Find candidate dimension labels — small integers + total-run "2,120"-style
        dims_with_pos: list[dict] = []
        for w in dim_words:
            text = w["text"].strip()
            if _DIM_RE.match(text) or _BIG_DIM_RE.match(text):
                try:
                    val = int(text.replace(",", ""))
                    if 10 <= val <= 5000:
                        dims_with_pos.append({
                            "val": val,
                            "x0": float(w["x0"]),
                            "x1": float(w["x1"]),
                            "y_top": float(w["top"]),
                            "y_bot": float(w["bottom"]),
                        })
                except ValueError:
                    pass

        # Plain integer values (for the existing ladder-extraction code)
        dims_xyv = [(d["x0"], d["y_top"], d["val"]) for d in dims_with_pos]

        evidence.plan_dimension_ladder, evidence.elevation_dimension_ladder = \
            _identify_two_ladders(dims_xyv)

        # Real pixel-accurate segment positions for the SVG overlay
        evidence.segments = _extract_segments_pixels(dims_with_pos, scale)

        # Finish-spec table (right side of page)
        evidence.finish_spec = _extract_finish_spec(words)

    return evidence


def _extract_segments_pixels(
    dims_with_pos: list[dict], scale: float
) -> list[CabinetSegment]:
    """Convert dimension labels into pixel-accurate cabinet segments.

    Logic:
    1. Cluster labels into horizontal y-bands (5pt tolerance).
    2. Find a "total-run" label — a 4-digit value like 2,120 or 2,600 that
       sits alone or near-alone in its band (the dimension-line label).
    3. Find the segment-ladder band immediately below it whose values SUM
       to approximately the total. That's the plan view's dimension row.
    4. Map each segment label to image pixels:
         - X: linear interpolation between leftmost-label-center and
           rightmost-label-center, with half-segment adjustment for the
           segments outside the labels.
         - Y: cabinet outline sits ~50pt below the labels, ~70pt tall
           (typical for LH detail drawings).
    """
    if not dims_with_pos:
        return []

    # Cluster by y-band
    bands: dict[int, list[dict]] = {}
    for d in dims_with_pos:
        key = int(d["y_top"] / 5) * 5
        bands.setdefault(key, []).append(d)

    sorted_bands = sorted(bands.items())

    # Find a "total-run" candidate: a single (or near-isolated) label with
    # value >=1500, NOT in a multi-label band (which would be a segment ladder).
    total_candidates = []
    for y, members in sorted_bands:
        big_labels = [d for d in members if d["val"] >= 1500]
        if big_labels and len(members) <= 2:
            # Looks like a "2,120" total-run label sitting alone above its segments
            for d in big_labels:
                total_candidates.append((y, d))

    if not total_candidates:
        return []

    # For each candidate, find the segment-ladder below it whose sum matches
    chosen_ladder: list[dict] | None = None
    for total_y, total_label in total_candidates:
        # Look for segment ladders below (within 30pt) whose sum ≈ total
        for y, members in sorted_bands:
            if y <= total_y or y > total_y + 30:
                continue
            if len(members) < 2:
                continue
            seg_sum = sum(d["val"] for d in members if d["val"] != total_label["val"])
            # Match within 1mm
            if abs(seg_sum - total_label["val"]) <= 1:
                # Filter out the total-run label itself if it's in this band
                chosen_ladder = sorted(
                    [d for d in members if d["val"] != total_label["val"]],
                    key=lambda d: d["x0"],
                )
                break
        if chosen_ladder:
            break

    if not chosen_ladder:
        return []

    segment_labels = chosen_ladder
    total_mm = sum(d["val"] for d in segment_labels)
    if total_mm == 0:
        return []

    # PDF run boundaries (approximate from leftmost-label-center to rightmost-label-center,
    # with adjustment for first/last half-segment that extends past the labels)
    first_label_center_pdf = (segment_labels[0]["x0"] + segment_labels[0]["x1"]) / 2
    last_label_center_pdf = (segment_labels[-1]["x0"] + segment_labels[-1]["x1"]) / 2

    # Half-widths in mm
    first_half_mm = segment_labels[0]["val"] / 2
    last_half_mm = segment_labels[-1]["val"] / 2
    inner_mm = total_mm - first_half_mm - last_half_mm
    inner_pdf = last_label_center_pdf - first_label_center_pdf

    if inner_mm <= 0 or inner_pdf <= 0:
        return []

    pdf_per_mm = inner_pdf / inner_mm
    run_start_pdf = first_label_center_pdf - first_half_mm * pdf_per_mm

    # Cabinet outline y-range: approximately ladder_y + offset
    ladder_y_pdf = min(d["y_top"] for d in segment_labels)
    # Typical LH layout: cabinet outline ~50pt below labels, ~70pt tall
    cabinet_top_pdf = ladder_y_pdf + 50
    cabinet_bot_pdf = ladder_y_pdf + 120

    # Compute each segment's pixel-accurate position
    segments: list[CabinetSegment] = []
    cum_mm = 0.0
    for d in segment_labels:
        x0_mm = cum_mm
        x1_mm = cum_mm + d["val"]
        x0_pdf = run_start_pdf + x0_mm * pdf_per_mm
        x1_pdf = run_start_pdf + x1_mm * pdf_per_mm

        segments.append(CabinetSegment(
            width_mm=d["val"],
            x0_px=x0_pdf * scale,
            x1_px=x1_pdf * scale,
            y0_px=cabinet_top_pdf * scale,
            y1_px=cabinet_bot_pdf * scale,
            band="plan",
        ))
        cum_mm += d["val"]

    return segments


def _identify_two_ladders(
    dims: list[tuple[float, float, int]]
) -> tuple[list[int], list[int]]:
    """Cluster dimension labels by y-coordinate to find horizontal ladders.

    The plan view's dimension ladder is one horizontal cluster of labels;
    the elevation view's is another. Both are expected to sum to the same
    total run width (e.g. 2,120mm for a 26㎡ kitchen).

    Returns (plan_ladder, elevation_ladder), with plan being the upper one
    on the page (lower y-coordinate, since PDF y starts at top).
    """
    if not dims:
        return [], []

    # Bucket dims into y-bands (tolerance 5px) — labels in a single ladder
    # share a near-identical y because they sit on a horizontal tick line.
    bands: dict[int, list[tuple[float, int]]] = {}
    for x, y, val in dims:
        band_key = int(y / 4) * 4
        bands.setdefault(band_key, []).append((x, val))

    # Filter: a ladder needs ≥4 labels (run-width + at least 3 segments)
    ladder_bands = [
        (band_key, members)
        for band_key, members in bands.items()
        if len(members) >= 4
    ]

    # Sort by y (top of page first)
    ladder_bands.sort()

    # Score each candidate by "looks like a dimension ladder":
    # - Has a "big" total-run number (> 1500mm, e.g. 2120, 2600)
    # - Other labels are smaller segment widths
    # - Bands closer to the top of the page are "plan view" by convention
    def score(band: tuple[int, list[tuple[float, int]]]) -> tuple[float, int]:
        _, members = band
        members_sorted = sorted(members)
        values = [v for _, v in members_sorted]
        has_big = any(v >= 1500 for v in values)
        return (1.0 if has_big else 0.0, len(members))

    ladder_bands.sort(key=score, reverse=True)

    # Take top 2 by ladder-likeness
    chosen = ladder_bands[:2]

    # Re-sort by y so plan (top) comes first
    chosen.sort()

    ladders: list[list[int]] = []
    for _, members in chosen:
        members.sort()
        # Drop the "big" total-run dimension (e.g. 2,120) from the ladder list —
        # we want only the segment widths.
        values = [v for _, v in members]
        segments = [v for v in values if v < 1500]
        ladders.append(segments)

    while len(ladders) < 2:
        ladders.append([])

    return ladders[0], ladders[1]


_SPEC_KEYS = [
    "문짝", "마감판넬", "체대", "선반", "걸레받이", "상판", "뒷선반",
    "장식판", "헤시아", "훼시아", "뒷판", "서랍밑판", "전기", "기계공사",
    "싱크볼", "손잡이", "악세사리", "비고",
]


def _extract_finish_spec(words: list[dict]) -> dict[str, str]:
    """Parse the right-side 주요자재사양 (finish spec) table.

    Heuristic: look for known Korean key labels; the corresponding value is
    typically the next text-block to the right on the same y-row.
    """
    spec: dict[str, str] = {}
    sorted_words = sorted(words, key=lambda w: (round(float(w["top"])), float(w["x0"])))

    for i, w in enumerate(sorted_words):
        text = w["text"].strip().rstrip(":")
        for key in _SPEC_KEYS:
            if key == text or text.startswith(key):
                # Find next word on same line (within 8px y) and to the right
                wy, wx = float(w["top"]), float(w["x1"])
                for j in range(i + 1, min(i + 30, len(sorted_words))):
                    other = sorted_words[j]
                    if abs(float(other["top"]) - wy) > 8:
                        continue
                    if float(other["x0"]) <= wx:
                        continue
                    spec[key] = other["text"].strip()
                    break
                break

    return spec


# -----------------------------------------------------------------------------
# Rendering (for vision model input + Streamlit UI display)
# -----------------------------------------------------------------------------
def render_page(pdf_path: str | Path, page_num: int, dpi: int = 200) -> Image.Image:
    """Render a PDF page as a PIL.Image, suitable for vision-model input."""
    doc = fitz.open(str(pdf_path))
    try:
        page = doc.load_page(page_num - 1)
        scale = dpi / 72
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return img
    finally:
        doc.close()


def render_pdf_pages(
    pdf_path: str | Path,
    pages: list[int] | None = None,
    dpi: int = 200,
) -> Iterator[tuple[int, Image.Image]]:
    """Render multiple pages, yielding (page_num, image) tuples."""
    doc = fitz.open(str(pdf_path))
    try:
        page_nums = pages if pages else range(1, len(doc) + 1)
        scale = dpi / 72
        for pn in page_nums:
            page = doc.load_page(pn - 1)
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            yield pn, img
    finally:
        doc.close()


# -----------------------------------------------------------------------------
# Smoke test (run as `python -m kbom.geometry.pdf_parser <pdf>`)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m kbom.geometry.pdf_parser <pdf_path>")
        sys.exit(1)

    pdf = sys.argv[1]
    print(f"\nIdentifying variants in {pdf}...\n")
    variants = identify_variants(pdf)
    for page, code, label in variants:
        print(f"  page {page:3d}  {code:6}  {label}")

    if variants:
        page = variants[0][0]
        print(f"\nExtracting geometry for page {page}...")
        ev = extract_geometry(pdf, page)
        print(f"  Plan ladder: {ev.plan_dimension_ladder}")
        print(f"  Elevation ladder: {ev.elevation_dimension_ladder}")
        print(f"  Finish spec: {ev.finish_spec}")
