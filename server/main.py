"""FastAPI service — wraps the kbom pipeline as a REST API for the Next.js frontend.

Endpoints:
  GET  /api/health
  GET  /api/projects                          List projects
  POST /api/projects/sample                   Demo: create from bundled sample
  POST /api/projects                          Upload PDF, create project
  GET  /api/projects/{id}                     Project detail
  DELETE /api/projects/{id}                   Delete project
  GET  /api/projects/{id}/variants/{code}     Variant detail
  POST /api/projects/{id}/variants/{code}/approve
  PATCH /api/projects/{id}/variants/{code}/rows/{i}  Inline edit
  POST /api/projects/{id}/variants/{code}/recalc     Trigger Excel recalc
  GET  /api/projects/{id}/blueprint/{page}.png       Render PDF page
  GET  /api/projects/{id}/download.xlsx              Download populated workbook
  GET  /api/rules                              Rule library

Persistence: JSON file at ./.kbom-state.json (state survives server restart).
"""
from __future__ import annotations

import io
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Make kbom importable
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from kbom.geometry import pdf_parser
from kbom.models import Category, RowSource
from kbom.pipeline import run_extraction
from kbom.rules.engine import list_rules

app = FastAPI(title="KBOM API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Storage layout
# -----------------------------------------------------------------------------
STATE_FILE = ROOT / ".kbom-state.json"
RUNS_DIR = ROOT / ".runs"
UPLOADS_DIR = ROOT / ".uploads"
RUNS_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)

SAMPLE_PDF = Path("/Users/d/Downloads/붙임3-2. 주방가구 상세도(화성태안3 A-2BL)-2.pdf")
SAMPLE_TEMPLATE = Path("/Users/d/Downloads/1. LH 화성태안3 A2BL-26A.xls")


# In-memory cache of projects (loaded from / persisted to STATE_FILE)
PROJECTS: dict[str, dict[str, Any]] = {}
# Extraction results live in RAM only — they include non-serializable objects.
# When the server restarts, we re-run extraction on demand.
EXTRACTION_CACHE: dict[str, Any] = {}


def _save_state() -> None:
    """Persist projects metadata (NOT extraction results) to disk."""
    serializable = {}
    for pid, p in PROJECTS.items():
        serializable[pid] = {
            "name": p["name"],
            "developer": p["developer"],
            "blueprint_pdf_path": p["blueprint_pdf_path"],
            "created_at": p["created_at"],
            "status": p["status"],
            "units_per_variant": p["units_per_variant"],
            "approved": list(p["approved"]),
            "variants_meta": [
                [page, code, label] for page, code, label in p["variants_meta"]
            ],
            "row_overrides": p.get("row_overrides", {}),
            "populated_xlsx": p.get("populated_xlsx"),
        }
    STATE_FILE.write_text(json.dumps(serializable, ensure_ascii=False, indent=2))


def _load_state() -> None:
    """Restore projects from disk on startup."""
    if not STATE_FILE.exists():
        return
    try:
        data = json.loads(STATE_FILE.read_text())
    except Exception:
        return
    for pid, p in data.items():
        PROJECTS[pid] = {
            "name": p["name"],
            "developer": p["developer"],
            "blueprint_pdf_path": p["blueprint_pdf_path"],
            "created_at": p["created_at"],
            "status": p["status"],
            "units_per_variant": p["units_per_variant"],
            "approved": set(p.get("approved", [])),
            "variants_meta": [tuple(v) for v in p.get("variants_meta", [])],
            "row_overrides": p.get("row_overrides", {}),
            "populated_xlsx": p.get("populated_xlsx"),
        }


def _get_extraction(pid: str):
    """Get the extraction result for a project, running it on demand if needed."""
    if pid in EXTRACTION_CACHE:
        return EXTRACTION_CACHE[pid]
    if pid not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    p = PROJECTS[pid]
    pdf_path = Path(p["blueprint_pdf_path"])
    if not pdf_path.exists():
        raise HTTPException(
            status_code=410, detail=f"Blueprint PDF missing: {pdf_path}"
        )
    result = run_extraction(
        pdf_path=pdf_path,
        template_path=SAMPLE_TEMPLATE,
        project_name=p["name"],
        units_per_variant=p["units_per_variant"],
        output_dir=RUNS_DIR / pid,
        skip_recalc=True,
    )
    # Apply any saved row overrides
    overrides = p.get("row_overrides", {})
    for v in result.project.variants:
        var_overrides = overrides.get(v.type_code, {})
        for idx_str, fields in var_overrides.items():
            i = int(idx_str)
            if 0 <= i < len(v.rows):
                row = v.rows[i]
                for k, val in fields.items():
                    if hasattr(row, k):
                        setattr(row, k, val)
                row.source = RowSource.HUMAN
                row.confidence = 1.0
    EXTRACTION_CACHE[pid] = result
    p["populated_xlsx"] = (
        str(result.populated_xlsx) if result.populated_xlsx else None
    )
    return result


_load_state()


# -----------------------------------------------------------------------------
# Pydantic schemas
# -----------------------------------------------------------------------------
class ProjectSummary(BaseModel):
    id: str
    name: str
    developer: str
    variants_count: int
    units_total: int
    approved_variants: int
    status: str
    created_at: str


class VariantSummary(BaseModel):
    code: str
    label: str
    page_number: int
    units: int
    rows_count: int
    flagged: int
    is_approved: bool


class ProjectDetail(ProjectSummary):
    variants: list[VariantSummary]
    blueprint_pdf_path: str


class RuleCitation(BaseModel):
    rule_id: str
    description: str
    document: str
    page: Optional[int] = None
    section_code: Optional[str] = None


class CabinetRowOut(BaseModel):
    index: int
    category: str
    code: str
    name: str
    width_mm: Optional[int] = None
    depth_mm: Optional[int] = None
    height_mm: Optional[int] = None
    type_label: str
    source: str
    confidence: float
    rule_citation: Optional[RuleCitation] = None


class ValidationOut(BaseModel):
    rule_id: str
    description: str
    passed: bool
    detail: str = ""


class VariantDetail(BaseModel):
    code: str
    label: str
    page_number: int
    units: int
    rows: list[CabinetRowOut]
    validations: list[ValidationOut]
    rules_fired: list[str]
    is_approved: bool
    cost_per_unit: Optional[int] = None
    cost_total: Optional[int] = None


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _row_to_out(i: int, r) -> CabinetRowOut:
    cite = None
    if r.rule_citation:
        cite = RuleCitation(
            rule_id=r.rule_citation.rule_id,
            description=r.rule_citation.description,
            document=r.rule_citation.document,
            page=r.rule_citation.page,
            section_code=r.rule_citation.section_code,
        )
    return CabinetRowOut(
        index=i,
        category=r.category.value,
        code=r.code,
        name=r.name,
        width_mm=r.width_mm,
        depth_mm=r.depth_mm,
        height_mm=r.height_mm,
        type_label=r.type_label,
        source=r.source.value,
        confidence=r.confidence,
        rule_citation=cite,
    )


def _to_summary(project_id: str, p: dict) -> ProjectSummary:
    return ProjectSummary(
        id=project_id,
        name=p["name"],
        developer=p["developer"],
        variants_count=len(p["variants_meta"]),
        units_total=sum(p["units_per_variant"].values()),
        approved_variants=len(p["approved"]),
        status=p["status"],
        created_at=p["created_at"],
    )


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.2.0", "projects": len(PROJECTS)}


@app.get("/api/projects", response_model=list[ProjectSummary])
def list_projects():
    items = sorted(
        PROJECTS.items(),
        key=lambda kv: kv[1]["created_at"],
        reverse=True,
    )
    return [_to_summary(pid, p) for pid, p in items]


@app.post("/api/projects/sample", response_model=ProjectDetail)
def create_sample_project():
    """Create a project from the bundled sample (no upload required)."""
    if not SAMPLE_PDF.exists():
        raise HTTPException(
            status_code=410,
            detail=f"Sample PDF missing at {SAMPLE_PDF}. Place the supplied PDF there or use POST /api/projects.",
        )
    return _create_project(
        pdf_path=SAMPLE_PDF,
        name="화성태안3 A2BL",
        units_per_variant={
            "26A": 120, "26A1": 80, "37A": 60, "37A1": 40,
            "37B": 50, "37B1": 30, "46A": 20,
        },
        developer="LH",
    )


@app.post("/api/projects", response_model=ProjectDetail)
async def create_project(
    name: str = Form(...),
    developer: str = Form("LH"),
    pdf: UploadFile = File(...),
):
    """Create a project from an uploaded PDF."""
    pdf_path = UPLOADS_DIR / f"{uuid.uuid4().hex[:8]}_{pdf.filename}"
    with open(pdf_path, "wb") as f:
        f.write(await pdf.read())
    return _create_project(
        pdf_path=pdf_path, name=name, units_per_variant={}, developer=developer
    )


def _create_project(
    pdf_path: Path,
    name: str,
    units_per_variant: dict[str, int],
    developer: str,
) -> ProjectDetail:
    pid = uuid.uuid4().hex[:8]

    variants_meta = pdf_parser.identify_variants(pdf_path)
    if not variants_meta:
        raise HTTPException(
            status_code=400,
            detail="No unit-type variants detected in the PDF. Check format.",
        )

    if not units_per_variant:
        units_per_variant = {code: 50 for _, code, _ in variants_meta}

    PROJECTS[pid] = {
        "name": name,
        "developer": developer,
        "blueprint_pdf_path": str(pdf_path),
        "created_at": datetime.now().isoformat(),
        "status": "Awaiting review",
        "units_per_variant": units_per_variant,
        "approved": set(),
        "variants_meta": variants_meta,
        "row_overrides": {},
        "populated_xlsx": None,
    }
    _save_state()

    # Trigger extraction (fills cache); 200ms for sample
    _get_extraction(pid)
    return _project_detail(pid)


def _project_detail(pid: str) -> ProjectDetail:
    if pid not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    p = PROJECTS[pid]
    summary = _to_summary(pid, p)
    extraction = _get_extraction(pid)
    variants = []
    for v in extraction.project.variants:
        variants.append(VariantSummary(
            code=v.type_code,
            label=v.variant_label,
            page_number=v.page_number,
            units=p["units_per_variant"].get(v.type_code, 0),
            rows_count=len(v.rows),
            flagged=v.num_flagged,
            is_approved=v.type_code in p["approved"],
        ))
    return ProjectDetail(
        **summary.model_dump(),
        variants=variants,
        blueprint_pdf_path=p["blueprint_pdf_path"],
    )


@app.get("/api/projects/{pid}", response_model=ProjectDetail)
def get_project(pid: str):
    return _project_detail(pid)


@app.delete("/api/projects/{pid}")
def delete_project(pid: str):
    if pid not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    PROJECTS.pop(pid)
    EXTRACTION_CACHE.pop(pid, None)
    _save_state()
    return {"deleted": pid}


@app.get("/api/projects/{pid}/variants/{code}", response_model=VariantDetail)
def get_variant(pid: str, code: str):
    if pid not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    p = PROJECTS[pid]
    extraction = _get_extraction(pid)
    for v in extraction.project.variants:
        if v.type_code == code:
            rows_out = [_row_to_out(i, r) for i, r in enumerate(v.rows)]
            rules_fired = sorted({
                r.rule_citation.rule_id for r in v.rows
                if r.rule_citation
            })
            cost_per_unit, cost_total = _compute_cost(rows_out, p["units_per_variant"].get(code, 1))
            return VariantDetail(
                code=v.type_code,
                label=v.variant_label,
                page_number=v.page_number,
                units=p["units_per_variant"].get(v.type_code, 0),
                rows=rows_out,
                validations=[ValidationOut(
                    rule_id=vr.rule_id,
                    description=vr.description,
                    passed=vr.passed,
                    detail=vr.detail,
                ) for vr in v.validations],
                rules_fired=rules_fired,
                is_approved=v.type_code in p["approved"],
                cost_per_unit=cost_per_unit,
                cost_total=cost_total,
            )
    raise HTTPException(status_code=404, detail=f"Variant {code} not found")


def _compute_cost(rows: list[CabinetRowOut], units: int) -> tuple[int, int]:
    """Heuristic per-unit cost — sums approximate prices per cabinet code/product.

    For a real production pipeline we'd run the LibreOffice recalc and read the
    real ₩ from 일위대가표 — but that's a 5-30s operation. For interactive UI we
    use this fast estimate.
    """
    # Rough KRW per 1000mm² for cabinets, plus product flat rates.
    per_unit = 0
    for r in rows:
        if r.category == "목대" and r.width_mm and r.depth_mm and r.height_mm:
            area = (r.width_mm * r.height_mm) / 1_000_000  # m²
            per_unit += int(area * 250_000)  # ~₩250k per m² of frontage
        elif r.category == "상품":
            # Rough product prices
            if "씽크볼" in r.name: per_unit += 32000
            elif "BMC" in r.name: per_unit += 172920
            elif "후크배수구" in r.name: per_unit += 14000
            elif "행거레일" in r.name: per_unit += 7500
            elif "2단컵걸이" in r.name: per_unit += 14000
            elif "칼꽂이" in r.name: per_unit += 2200
            else: per_unit += 5000
    # Add labor + overhead (~30% of materials)
    per_unit = int(per_unit * 1.3)
    return per_unit, per_unit * units


class ApproveBody(BaseModel):
    approved: bool = True


@app.post("/api/projects/{pid}/variants/{code}/approve")
def approve_variant(pid: str, code: str, body: ApproveBody):
    if pid not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    p = PROJECTS[pid]
    if body.approved:
        p["approved"].add(code)
    else:
        p["approved"].discard(code)
    if len(p["approved"]) == len(p["variants_meta"]):
        p["status"] = "Approved"
    elif p["approved"]:
        p["status"] = "In review"
    else:
        p["status"] = "Awaiting review"
    _save_state()
    return {"approved": body.approved, "project_status": p["status"]}


class RowUpdate(BaseModel):
    width_mm: Optional[int] = None
    depth_mm: Optional[int] = None
    height_mm: Optional[int] = None
    code: Optional[str] = None
    name: Optional[str] = None


@app.patch("/api/projects/{pid}/variants/{code}/rows/{i}", response_model=CabinetRowOut)
def update_row(pid: str, code: str, i: int, update: RowUpdate):
    """Inline edit a row. Marks source=HUMAN; persists the override."""
    if pid not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    p = PROJECTS[pid]
    extraction = _get_extraction(pid)
    for v in extraction.project.variants:
        if v.type_code == code:
            if i < 0 or i >= len(v.rows):
                raise HTTPException(status_code=404, detail="Row not found")
            row = v.rows[i]
            changes: dict[str, Any] = {}
            for field in ("width_mm", "depth_mm", "height_mm", "code", "name"):
                val = getattr(update, field)
                if val is not None:
                    setattr(row, field, val)
                    changes[field] = val
            row.source = RowSource.HUMAN
            row.confidence = 1.0
            # Persist the override
            overrides = p.setdefault("row_overrides", {})
            var_overrides = overrides.setdefault(code, {})
            existing = var_overrides.setdefault(str(i), {})
            existing.update(changes)
            _save_state()
            return _row_to_out(i, row)
    raise HTTPException(status_code=404, detail=f"Variant {code} not found")


@app.get("/api/projects/{pid}/blueprint/{page}.png")
def get_blueprint_page(pid: str, page: int, dpi: int = 150):
    if pid not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    pdf_path = PROJECTS[pid]["blueprint_pdf_path"]
    img = pdf_parser.render_page(pdf_path, page, dpi=dpi)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@app.get("/api/projects/{pid}/download.xlsx")
def download_workbook(pid: str):
    """Download the populated Excel workbook for a project."""
    if pid not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    p = PROJECTS[pid]
    populated = p.get("populated_xlsx")
    if not populated or not Path(populated).exists():
        # Trigger extraction to produce it
        _get_extraction(pid)
        populated = p.get("populated_xlsx")
    if not populated:
        raise HTTPException(status_code=500, detail="Workbook not yet populated")
    return FileResponse(
        populated,
        filename=f"{p['name']}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.get("/api/rules")
def get_rules():
    return list_rules()
