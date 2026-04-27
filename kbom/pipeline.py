"""End-to-end pipeline orchestrator.

Walks a blueprint PDF through every stage:
  1. Identify variants (PDF parser)
  2. For each variant: render page → vision extract → apply rules
  3. Populate Excel template → recalc → read computed values
  4. Return a populated Project object ready for the UI to render

This is the function the Streamlit app calls when the user clicks
"Start Extraction" on the project setup screen.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from kbom.excel import populator as excel_populator
from kbom.excel import recalc as excel_recalc
from kbom.excel import reader as excel_reader
from kbom.geometry import pdf_parser
from kbom.models import (
    CabinetRow,
    Project,
    VariantExtraction,
    ValidationResult,
)
from kbom.rules import engine as rules_engine
from kbom.vision import claude_extractor


@dataclass
class ExtractionResult:
    """Output of running the pipeline on one project."""

    project: Project
    populated_xlsx: Optional[Path] = None       # path to the recalculated workbook
    workbook_snapshot: Optional[excel_reader.WorkbookSnapshot] = None


def run_extraction(
    pdf_path: str | Path,
    template_path: str | Path,
    project_name: str = "",
    units_per_variant: dict[str, int] | None = None,
    output_dir: str | Path | None = None,
    skip_recalc: bool = False,
) -> ExtractionResult:
    """Full pipeline: PDF + Excel template → populated, recalculated workbook.

    Args:
        pdf_path: Customer's blueprint PDF
        template_path: Customer's Excel template (the 18-tab one)
        project_name: e.g. "화성태안3 A2BL" (auto-detected if blank)
        units_per_variant: optional dict like {"26A": 120, "26A1": 80, ...}
        output_dir: where to put the populated/recalc'd workbook
        skip_recalc: for fast prototyping — skip the LibreOffice step
    """
    pdf_path = Path(pdf_path)
    template_path = Path(template_path)
    out_dir = Path(output_dir) if output_dir else pdf_path.parent / "kbom_runs"
    out_dir.mkdir(parents=True, exist_ok=True)

    project_name = project_name or pdf_path.stem

    # Step 1: Identify variants
    variants_meta = pdf_parser.identify_variants(pdf_path)

    project = Project(
        name=project_name,
        developer="LH",
        blueprint_pdf_path=str(pdf_path),
    )

    # Step 2: Per-variant extract → rules
    for page_num, type_code, label in variants_meta:
        variant = _extract_variant(pdf_path, page_num, type_code, label)
        project.variants.append(variant)

    # Step 3: Populate template + recalc + read
    # For Stage 1 prototype, we populate the template using the FIRST variant's
    # rows. (Full multi-variant projects need a per-variant workbook copy or a
    # template that supports multiple variants — out of MVP scope.)
    populated_path: Path | None = None
    snapshot = None
    if project.variants:
        first = project.variants[0]
        populated_path = out_dir / f"{pdf_path.stem}__{first.type_code}.xlsx"

        excel_populator.populate_template(
            template_path=template_path,
            output_path=populated_path,
            rows=first.rows,
            type_label=first.type_code,
            units_count=(units_per_variant or {}).get(first.type_code, 1),
        )

        if not skip_recalc:
            try:
                recalc_dir = out_dir / "_recalc"
                populated_path = excel_recalc.recalc(populated_path, output_dir=recalc_dir)
                snapshot = excel_reader.read_workbook(populated_path)
            except RuntimeError as e:
                # Recalc failed (e.g. LibreOffice unavailable); continue without
                print(f"[pipeline] Recalc skipped: {e}")

    return ExtractionResult(
        project=project,
        populated_xlsx=populated_path,
        workbook_snapshot=snapshot,
    )


def _extract_variant(
    pdf_path: Path, page_num: int, type_code: str, label: str
) -> VariantExtraction:
    """Run extraction + rules for a single variant page."""
    # Geometry hints (deterministic)
    geometry = pdf_parser.extract_geometry(pdf_path, page_num)

    # Render the page for vision
    page_image = pdf_parser.render_page(pdf_path, page_num, dpi=200)

    # Vision extraction (live API or synthetic)
    raw_rows = claude_extractor.extract(page_image, type_label=type_code)

    # Apply rules
    augmented = rules_engine.apply_rules(raw_rows, type_label=type_code)

    # Validations
    validations = _run_validations(augmented, geometry)

    return VariantExtraction(
        variant_label=label,
        type_code=type_code,
        page_number=page_num,
        rows=augmented,
        geometry=geometry,
        validations=validations,
    )


def _run_validations(
    rows: list[CabinetRow], geometry
) -> list[ValidationResult]:
    """Run sanity checks on an extracted variant."""
    results: list[ValidationResult] = []

    # V1: All cabinet codes present in the LH catalog
    from kbom.catalog.lh_v2025 import CABINET_TYPES
    unknown = [r.code for r in rows if r.code and r.code not in CABINET_TYPES]
    results.append(ValidationResult(
        rule_id="V1",
        description="All cabinet codes are in the LH catalog vocabulary",
        passed=not unknown,
        detail=f"Unknown codes: {unknown}" if unknown else "OK",
    ))

    # V2: Range-base height matches the recessed-hob convention
    range_bases = [r for r in rows if r.code in ("BR", "CR")]
    range_ok = all(r.height_mm == 550 for r in range_bases)
    results.append(ValidationResult(
        rule_id="V2",
        description="Range-base height = 550mm (recessed hob, rule R6)",
        passed=range_ok or not range_bases,
        detail="OK" if range_ok else "Range base height not corrected",
    ))

    # V3: Sink base accommodates the sink bowl
    sink_bases = [r for r in rows if r.code == "CS" or r.code == "BS"]
    has_630_sink = any(
        "630" in r.name for r in rows if r.category.value == "상품" and "씽크볼" in r.name
    )
    if sink_bases and has_630_sink:
        ok = all(r.width_mm and r.width_mm >= 630 + 80 for r in sink_bases)
        results.append(ValidationResult(
            rule_id="V3",
            description="Sink base ≥ sink + clearance (80mm)",
            passed=ok,
            detail="OK" if ok else "Sink base may be too narrow",
        ))

    return results
