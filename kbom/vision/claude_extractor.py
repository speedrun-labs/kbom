"""Claude vision wrapper — extracts cabinet rows from a rendered blueprint page.

Two modes:
- live mode: actually calls Anthropic API (requires ANTHROPIC_API_KEY)
- synthetic mode: returns the known Phase-0 ground-truth-ish output (for fast
  prototype iteration without API costs / latency)

The synthetic mode is calibrated against the 26㎡ A형 sample we already
validated. It mimics the *imperfect* vision output (76% strict match, with
the systematic errors that R1–R8 fix) so the rest of the pipeline can be
exercised end-to-end.
"""
from __future__ import annotations

import base64
import io
import json
import os
from pathlib import Path

from PIL import Image

from kbom.models import CabinetRow, Category, RowSource


# -----------------------------------------------------------------------------
# Synthetic mode — fast, free, deterministic for the 26A sample.
# -----------------------------------------------------------------------------
def synthetic_extract_26A() -> list[CabinetRow]:
    """The blind-vision output for 26㎡ A형 from Phase 0 Test 3.

    Mirrors what Claude's vision produced on the actual blueprint, INCLUDING
    the systematic errors that downstream rules will fix. Total: 16 rows
    (5 missing vs ground truth 21; rules will add R2/R3/R4/R5/R8).
    """
    return [
        # Wall-cab assembly — vision sees panels with wrong W/D (R7 will fix)
        CabinetRow(category=Category.MOKDAE, code="WP", name="벽장판넬",
                   width_mm=20, depth_mm=290, height_mm=800,
                   type_label="26A", source=RowSource.VISION, confidence=0.55),
        CabinetRow(category=Category.MOKDAE, code="W", name="일반벽장",
                   width_mm=260, depth_mm=290, height_mm=800,
                   type_label="26A", source=RowSource.VISION, confidence=0.85),
        CabinetRow(category=Category.MOKDAE, code="WP", name="벽장판넬",
                   width_mm=20, depth_mm=290, height_mm=800,
                   type_label="26A", source=RowSource.VISION, confidence=0.55),
        CabinetRow(category=Category.MOKDAE, code="WP", name="벽장판넬",
                   width_mm=20, depth_mm=290, height_mm=800,
                   type_label="26A", source=RowSource.VISION, confidence=0.55),
        CabinetRow(category=Category.MOKDAE, code="W", name="일반벽장",
                   width_mm=380, depth_mm=290, height_mm=800,
                   type_label="26A", source=RowSource.VISION, confidence=0.85),
        CabinetRow(category=Category.MOKDAE, code="W", name="일반벽장",
                   width_mm=800, depth_mm=290, height_mm=800,
                   type_label="26A", source=RowSource.VISION, confidence=0.90),
        CabinetRow(category=Category.MOKDAE, code="WP", name="벽장판넬",
                   width_mm=20, depth_mm=290, height_mm=800,
                   type_label="26A", source=RowSource.VISION, confidence=0.55),
        # Base run — CR has wrong height (R6 will fix)
        CabinetRow(category=Category.MOKDAE, code="C", name="찬넬밑장",
                   width_mm=280, depth_mm=570, height_mm=700,
                   type_label="26A", source=RowSource.VISION, confidence=0.70),
        CabinetRow(category=Category.MOKDAE, code="CR", name="찬넬렌지밑장",
                   width_mm=600, depth_mm=570, height_mm=700,
                   type_label="26A", source=RowSource.VISION, confidence=0.78),
        CabinetRow(category=Category.MOKDAE, code="CD3", name="찬넬3단서랍밑장",
                   width_mm=400, depth_mm=570, height_mm=700,
                   type_label="26A", source=RowSource.VISION, confidence=0.75),
        CabinetRow(category=Category.MOKDAE, code="CS", name="찬넬씽크밑장",
                   width_mm=800, depth_mm=570, height_mm=700,
                   type_label="26A", source=RowSource.VISION, confidence=0.95),
        # Products from spec table (vision read 5 of 6; R8 will add the 6th)
        CabinetRow(category=Category.SANGPUM, code="", name="씽크볼(630용) 수세미망 포함",
                   type_label="26A", source=RowSource.SPEC_TABLE, confidence=0.95),
        CabinetRow(category=Category.SANGPUM, code="", name="BMC상판",
                   type_label="26A", source=RowSource.SPEC_TABLE, confidence=0.90),
        CabinetRow(category=Category.SANGPUM, code="", name="후크배수구",
                   type_label="26A", source=RowSource.SPEC_TABLE, confidence=0.75),
        CabinetRow(category=Category.SANGPUM, code="", name="칼꽂이",
                   type_label="26A", source=RowSource.SPEC_TABLE, confidence=0.80),
        CabinetRow(category=Category.SANGPUM, code="", name="행거레일",
                   type_label="26A", source=RowSource.SPEC_TABLE, confidence=0.70),
    ]


# -----------------------------------------------------------------------------
# Live mode (Anthropic API)
# -----------------------------------------------------------------------------
_VISION_PROMPT_TEMPLATE = """You are extracting a Bill of Materials (BOM) from a Korean kitchen blueprint.

The image is one page of an LH (Korea Land & Housing Corporation) standard kitchen detail drawing.
Identify every cabinet, panel, trim, sink, and accessory shown. For each, return a JSON object with:
  - category: "목대" (custom frame part) or "상품" (off-the-shelf product)
  - code: short cabinet code (WP, W, BI, BP, C, CR, CD3, CS, FA, PL for 목대; "" for 상품)
  - name: the Korean name (e.g. 벽장판넬, 일반벽장, 찬넬씽크밑장, 씽크볼)
  - width_mm, depth_mm, height_mm: dimensions in millimeters (omit for 상품)
  - confidence: 0.0–1.0 how certain you are

Output a JSON object: {"variant": "26A", "rows": [...]}

Important conventions:
- The dimension ladder at the top of the plan view shows segment widths
- The right-side spec table lists product names (씽크볼, BMC상판, 후크배수구, etc.)
- Cabinet end panels (벽장판넬, WP) are 20mm thick — read W and D carefully
- Range bases (찬넬렌지밑장, CR) are 550mm tall (recessed hob) not 700mm
"""


def live_extract(
    page_image: Image.Image,
    type_label: str = "26A",
    api_key: str | None = None,
) -> list[CabinetRow]:
    """Call Claude vision API on the rendered blueprint page.

    Falls back to synthetic mode if no API key is set.
    """
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        # Fallback: return the known synthetic output for prototype demos
        return synthetic_extract_26A()

    try:
        import anthropic  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "anthropic package not installed. `pip install anthropic`."
        ) from e

    client = anthropic.Anthropic(api_key=api_key)

    # Encode image as base64 PNG
    buf = io.BytesIO()
    page_image.save(buf, format="PNG")
    img_b64 = base64.standard_b64encode(buf.getvalue()).decode()

    response = client.messages.create(
        model="claude-opus-4-5-20251001",  # update to current model
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": _VISION_PROMPT_TEMPLATE,
                    },
                ],
            }
        ],
    )

    text = response.content[0].text  # type: ignore
    # Extract JSON from response
    json_text = text[text.find("{"): text.rfind("}") + 1]
    data = json.loads(json_text)

    rows: list[CabinetRow] = []
    for r in data.get("rows", []):
        rows.append(CabinetRow(
            category=Category(r["category"]),
            code=r.get("code", ""),
            name=r["name"],
            width_mm=r.get("width_mm"),
            depth_mm=r.get("depth_mm"),
            height_mm=r.get("height_mm"),
            type_label=type_label,
            source=RowSource.VISION if r.get("category") == "목대" else RowSource.SPEC_TABLE,
            confidence=r.get("confidence", 0.5),
        ))
    return rows


def extract(page_image: Image.Image, type_label: str = "26A") -> list[CabinetRow]:
    """Extract cabinet rows from a blueprint page.

    Uses live API if ANTHROPIC_API_KEY is set; otherwise synthetic mode.
    Synthetic mode currently only models the 26A sample.
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        return live_extract(page_image, type_label=type_label)
    return synthetic_extract_26A()
