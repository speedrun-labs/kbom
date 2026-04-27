"""Core data models for the KBOM pipeline.

These classes flow through every pipeline stage:
  PDF parser → Vision → Rules → Excel populator → Excel recalc → Reader → UI

Naming convention: Korean names preserved verbatim (they're the canonical
identifiers in the customer's Excel template); English glosses live in docstrings.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# -----------------------------------------------------------------------------
# Source provenance — where a row came from (the "why" behind every value).
# -----------------------------------------------------------------------------
class RowSource(str, Enum):
    """Where this BOM row originated."""

    VISION = "vision"          # AI-extracted from blueprint via Claude
    RULE = "rule"              # Emitted by domain rule (e.g. always-emit trim)
    CATALOG = "catalog"        # Standard accessory pulled from developer catalog
    SPEC_TABLE = "spec_table"  # Read from the PDF's finish-spec table
    HUMAN = "human"            # Manually entered/edited by reviewer


@dataclass(frozen=True)
class RuleCitation:
    """Citation for a rule that fired.

    Used by the cell inspector to show 'this row exists because rule R5 from
    LH catalog page 561 says baseboard is always 150×20×2400'.
    """

    rule_id: str                     # e.g. "R5"
    description: str                 # human-readable rule statement
    document: str                    # e.g. "LH 표준상세도 V2025.01"
    page: Optional[int] = None       # PDF page number in the cited document
    section_code: Optional[str] = None  # e.g. "DA-91-116"


# -----------------------------------------------------------------------------
# CabinetRow — one row of the cabinet/product BOM. Maps to a row in 장등록 or
# 상품등록 sheet of the customer's Excel template.
# -----------------------------------------------------------------------------
class Category(str, Enum):
    """Whether this row is a custom-fabricated frame part or an off-the-shelf product."""

    MOKDAE = "목대"     # custom frame parts (panels, cabinets, drawers)
    SANGPUM = "상품"    # off-the-shelf products (sink, countertop, accessories)


@dataclass
class CabinetRow:
    """One row of the BOM. Maps to a row in 장등록 (목대) or 상품등록 (상품)."""

    category: Category
    code: str                        # e.g. "WP" (wall panel), "CS" (sink base)
    name: str                        # Korean name, e.g. "벽장판넬", "찬넬씽크밑장"
    width_mm: Optional[int] = None   # 목대 only
    depth_mm: Optional[int] = None   # 목대 only
    height_mm: Optional[int] = None  # 목대 only
    type_label: str = ""             # e.g. "26A" — links row to assumption sheet
    qty: int = 1

    # Provenance
    source: RowSource = RowSource.VISION
    confidence: float = 1.0
    rule_citation: Optional[RuleCitation] = None
    source_evidence: Optional[str] = None  # free-text where this came from

    # Audit
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    is_approved: bool = False

    def is_dimensional(self) -> bool:
        """True for 목대 rows (have W/D/H); False for 상품."""
        return self.category == Category.MOKDAE


# -----------------------------------------------------------------------------
# Extraction artifacts.
# -----------------------------------------------------------------------------
@dataclass
class GeometryEvidence:
    """What the geometry adapter (PDF parser, DXF parser, etc.) saw on the page.

    Path A populates dimension_ladders and text_at_position; Path B/C add polygons
    and block_names. Common interface lets downstream code work with any source.
    """

    plan_dimension_ladder: list[int] = field(default_factory=list)        # e.g. [20, 280, 600, 400, 800, 20]
    elevation_dimension_ladder: list[int] = field(default_factory=list)
    section_depth_mm: Optional[int] = None
    section_height_mm: Optional[int] = None
    title_block_text: str = ""
    finish_spec: dict[str, str] = field(default_factory=dict)             # e.g. {"싱크볼": "630 언더싱크용", ...}
    raw_text_strings: list[str] = field(default_factory=list)             # for debugging

    # Path B/C only — empty in Path A
    polygons: list[dict] = field(default_factory=list)
    block_names: list[str] = field(default_factory=list)


@dataclass
class VariantExtraction:
    """All BOM rows extracted for one unit-type variant of one project."""

    variant_label: str               # e.g. "26㎡ A형 (일반형)"
    type_code: str                   # e.g. "26A"
    page_number: int                 # in the source PDF
    rows: list[CabinetRow] = field(default_factory=list)
    geometry: Optional[GeometryEvidence] = None
    validations: list["ValidationResult"] = field(default_factory=list)

    @property
    def num_flagged(self) -> int:
        return sum(1 for r in self.rows if r.confidence < 0.85 and r.source == RowSource.VISION)


@dataclass
class ValidationResult:
    """Output of a validation check (e.g. 'segment widths sum to total run')."""

    rule_id: str
    description: str
    passed: bool
    detail: str = ""


@dataclass
class Project:
    """A construction project — typically one apartment building with multiple unit-type variants."""

    name: str                        # e.g. "화성태안3 A2BL"
    developer: str                   # e.g. "LH"
    variants: list[VariantExtraction] = field(default_factory=list)
    blueprint_pdf_path: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def total_units(self) -> int:
        # In MVP the unit-count is held outside this class; stub for now.
        return 0
