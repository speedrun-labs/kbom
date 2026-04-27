"""Rule engine — applies R1–R23 to vision-extracted rows.

R1–R8 inferred from round-trip test on NEFS 26A sample (Phase 0).
R9–R23 mined from LH 표준상세도 V2025.01 (Phase 0 standards-mining pass).

Each rule is a callable that takes an in-progress list of CabinetRow and
optionally adds/edits rows. Rules are pure functions; order matters where
noted in the docstrings.
"""
from __future__ import annotations

from typing import Callable

from kbom.catalog.lh_v2025 import CABINET_TYPES, code_to_name
from kbom.models import CabinetRow, Category, RowSource, RuleCitation


# Source documents we cite from
LH_CATALOG = "LH 표준상세도 V2025.01"
PHASE0_ROUND_TRIP = "Phase 0 round-trip test (NEFS 26A sample)"


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _make_panel_row(code: str, w: int, d: int, h: int, type_label: str,
                    rule_id: str, description: str, document: str,
                    page: int | None = None, section: str | None = None) -> CabinetRow:
    """Create a panel/trim row emitted by a rule."""
    return CabinetRow(
        category=Category.MOKDAE,
        code=code,
        name=code_to_name(code),
        width_mm=w,
        depth_mm=d,
        height_mm=h,
        type_label=type_label,
        source=RowSource.RULE,
        confidence=1.0,
        rule_citation=RuleCitation(
            rule_id=rule_id,
            description=description,
            document=document,
            page=page,
            section_code=section,
        ),
    )


def _make_product_row(name: str, type_label: str,
                      rule_id: str, description: str) -> CabinetRow:
    """Create a 상품 row emitted by a rule."""
    return CabinetRow(
        category=Category.SANGPUM,
        code="",
        name=name,
        type_label=type_label,
        source=RowSource.CATALOG,
        confidence=1.0,
        rule_citation=RuleCitation(
            rule_id=rule_id,
            description=description,
            document=LH_CATALOG,
        ),
    )


# -----------------------------------------------------------------------------
# R1–R8 — round-trip-derived rules (Phase 0)
# -----------------------------------------------------------------------------
def r1_outer_wall_panels_taller(rows: list[CabinetRow]) -> list[CabinetRow]:
    """R1: The outer wall-panel rows on each end of the upper-cab run get
    bumped to 860mm height (vs. 800 for inner panels) — to include the top cap.

    Order-dependent: applies to first and last 벽장판넬 (WP) row in row order.
    """
    panel_rows = [r for r in rows if r.code == "WP"]
    if len(panel_rows) >= 2:
        for r in [panel_rows[0], panel_rows[-1]]:
            if r.height_mm != 860:
                r.height_mm = 860
                r.rule_citation = RuleCitation(
                    rule_id="R1",
                    description="Outer wall-cab end panels are 860mm (include top cap)",
                    document=PHASE0_ROUND_TRIP,
                )
    return rows


def r2_base_end_panel(rows: list[CabinetRow], type_label: str) -> list[CabinetRow]:
    """R2: Add a base end panel (밑장판넬, 650×20×850) at the fridge-adjacent
    end of the base-cabinet run. Always present in LH 26A units.
    """
    if not any(r.code == "BP" for r in rows):
        rows.append(_make_panel_row(
            "BP", 650, 20, 850, type_label,
            "R2",
            "Base end panel adjacent to refrigerator (650×20×850)",
            LH_CATALOG, page=555, section="DA-91-018",
        ))
    return rows


def r3_base_filler(rows: list[CabinetRow], type_label: str) -> list[CabinetRow]:
    """R3: Add a base filler panel (밑장휠라, 150×20×850) between the base run
    and the wall.
    """
    if not any(r.code == "BI" for r in rows):
        rows.append(_make_panel_row(
            "BI", 150, 20, 850, type_label,
            "R3",
            "Base filler panel between cabinet run and wall (150×20×850)",
            PHASE0_ROUND_TRIP,
        ))
    return rows


def r4_fascia_trim(rows: list[CabinetRow], type_label: str) -> list[CabinetRow]:
    """R4: Always emit fascia trim (장식판, 60×20×2400) per LH standard.

    Cited rule: 'If total length ≤ 2400mm, use single piece' (DA-91-116).
    NEFS Excel sizes 장식판 at exactly 2400mm.
    """
    if not any(r.code == "FA" for r in rows):
        rows.append(_make_panel_row(
            "FA", 60, 20, 2400, type_label,
            "R4",
            "Fascia trim 60×20×2400 (single piece per LH stock ceiling)",
            LH_CATALOG, page=561, section="DA-91-116",
        ))
    return rows


def r5_baseboard(rows: list[CabinetRow], type_label: str) -> list[CabinetRow]:
    """R5: Always emit baseboard (걸레받이, 150×20×2400) per LH standard.

    Same 2400mm stock-ceiling rule as fascia.
    """
    if not any(r.code == "PL" for r in rows):
        rows.append(_make_panel_row(
            "PL", 150, 20, 2400, type_label,
            "R5",
            "Baseboard 150×20×2400 (single piece per LH stock ceiling)",
            LH_CATALOG, page=561, section="DA-91-116",
        ))
    return rows


def r6_range_base_height(rows: list[CabinetRow]) -> list[CabinetRow]:
    """R6: Range-base cabinets (BR, CR, 찬넬렌지밑장) always use H=550mm,
    not 700mm — the cooktop is recessed into the cabinet body.

    Vision often reads 700 (default base height) for these; rule corrects.
    """
    for r in rows:
        if r.code in ("BR", "CR") or r.name == "찬넬렌지밑장":
            if r.height_mm and r.height_mm != 550:
                r.height_mm = 550
                r.rule_citation = RuleCitation(
                    rule_id="R6",
                    description="Range-base height = 550mm (recessed hob)",
                    document=LH_CATALOG,
                    page=567,
                    section_code="DA-91-150",
                )
    return rows


def r7_wall_panel_dimensions(rows: list[CabinetRow]) -> list[CabinetRow]:
    """R7: Vision often reads the 20mm THICKNESS of a wall-cab end panel as
    its width. Swap: panels should be 310W × 20D, not 20W × ?D.
    """
    for r in rows:
        if r.code == "WP" and r.width_mm == 20:
            r.width_mm = 310
            r.depth_mm = 20
            if not r.rule_citation:
                r.rule_citation = RuleCitation(
                    rule_id="R7",
                    description="Wall-panel dimensions corrected: 310W × 20D × H",
                    document=PHASE0_ROUND_TRIP,
                )
    return rows


def r8_standard_accessories(rows: list[CabinetRow], type_label: str) -> list[CabinetRow]:
    """R8: LH standard accessories always include 2단컵걸이선반 (2-tier cup
    shelf), even though it doesn't always appear in the spec table on every
    blueprint page.
    """
    if not any(r.name == "2단컵걸이선반" for r in rows):
        rows.append(_make_product_row(
            "2단컵걸이선반", type_label,
            "R8",
            "LH catalog: every kitchen unit includes 2단컵걸이선반",
        ))
    return rows


# -----------------------------------------------------------------------------
# R9–R16 — first standards-mining pass (cabinet-side details)
# -----------------------------------------------------------------------------
# These are mostly *informational* — they describe constraints for validation
# rather than emit new rows. The rules engine applies them as validators or
# annotations rather than mutators. (See r_validation_pass below.)


# -----------------------------------------------------------------------------
# R17–R23 — install-side rules (construction-finish installation limits)
# -----------------------------------------------------------------------------
# Same pattern: these annotate the install BOM (Phase 3b) rather than the
# cabinet BOM. Stub here for Stage 1; full implementation when Phase 3b ships.


# -----------------------------------------------------------------------------
# Top-level orchestrator
# -----------------------------------------------------------------------------
RuleFn = Callable[[list[CabinetRow]], list[CabinetRow]]


def apply_rules(rows: list[CabinetRow], type_label: str = "26A") -> list[CabinetRow]:
    """Apply the full R1–R8 rule chain in the correct order.

    Order matters in two places:
    - R7 must run before R1 (R7 fixes panel dims, then R1 bumps outer-panel H).
    - All "always-emit" rules (R2–R5, R8) run after the above so they don't
      interfere with vision-emitted rows.
    """
    rows = list(rows)

    # 1. Correct vision misreads
    rows = r7_wall_panel_dimensions(rows)
    rows = r6_range_base_height(rows)
    rows = r1_outer_wall_panels_taller(rows)

    # 2. Always-emit panels and trim
    rows = r2_base_end_panel(rows, type_label)
    rows = r3_base_filler(rows, type_label)
    rows = r4_fascia_trim(rows, type_label)
    rows = r5_baseboard(rows, type_label)

    # 3. Standard products
    rows = r8_standard_accessories(rows, type_label)

    return rows


def list_rules() -> list[dict]:
    """Returns rule metadata for use in the cell inspector / rules-fired sidebar."""
    return [
        {"id": "R1", "description": "Outer wall-cab end panels = 860mm height (include top cap)", "source": PHASE0_ROUND_TRIP},
        {"id": "R2", "description": "Add base end panel (BP, 650×20×850) at fridge-adjacent end", "source": LH_CATALOG, "section": "DA-91-018"},
        {"id": "R3", "description": "Add base filler (BI, 150×20×850) between run and wall", "source": PHASE0_ROUND_TRIP},
        {"id": "R4", "description": "Always emit fascia trim 장식판 60×20×2400", "source": LH_CATALOG, "section": "DA-91-116"},
        {"id": "R5", "description": "Always emit baseboard 걸레받이 150×20×2400", "source": LH_CATALOG, "section": "DA-91-116"},
        {"id": "R6", "description": "Range-base height = 550mm (recessed hob)", "source": LH_CATALOG, "section": "DA-91-150"},
        {"id": "R7", "description": "Wall-panel dimensions: swap 20W → 310W (vision often misreads thickness as width)", "source": PHASE0_ROUND_TRIP},
        {"id": "R8", "description": "Standard accessory 2단컵걸이선반 always included", "source": "LH accessory catalog"},
    ]
