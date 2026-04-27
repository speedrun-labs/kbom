"""FastAPI service — wraps the kbom pipeline as a REST API for the Next.js frontend.

Endpoints:
  GET  /api/projects                          List all projects
  POST /api/projects                          Create project (upload PDF, set name, units)
  GET  /api/projects/{id}                     Project detail
  GET  /api/projects/{id}/variants/{code}     Variant detail (rows + validations)
  POST /api/projects/{id}/variants/{code}/approve   Approve a variant
  POST /api/projects/{id}/variants/{code}/rows/{i}  Update a single row (inline edit)
  GET  /api/projects/{id}/blueprint/{page}    Render PDF page as PNG
  GET  /api/cells/{project_id}/{sheet}/{coord}  Cell inspector data (formula + provenance)

Storage: in-memory dict for prototype. Postgres comes in Stage 2.
"""
from __future__ import annotations

import io
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

# Make kbom importable
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from kbom.geometry import pdf_parser
from kbom.models import RowSource
from kbom.pipeline import run_extraction
from kbom.rules.engine import list_rules

app = FastAPI(title="KBOM API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# In-memory storage (Stage 1 prototype only)
# -----------------------------------------------------------------------------
PROJECTS: dict[str, dict[str, Any]] = {}
SAMPLE_PDF = Path("/Users/d/Downloads/붙임3-2. 주방가구 상세도(화성태안3 A-2BL)-2.pdf")
SAMPLE_TEMPLATE = Path("/Users/d/Downloads/1. LH 화성태안3 A2BL-26A.xls")
UPLOAD_DIR = Path("/tmp/kbom_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# -----------------------------------------------------------------------------
# Pydantic schemas (response shapes)
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
    page: int | None = None
    section_code: str | None = None


class CabinetRowOut(BaseModel):
    index: int
    category: str
    code: str
    name: str
    width_mm: int | None = None
    depth_mm: int | None = None
    height_mm: int | None = None
    type_label: str
    source: str
    confidence: float
    rule_citation: RuleCitation | None = None


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
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/projects", response_model=list[ProjectSummary])
def list_projects():
    return [_to_summary(pid, p) for pid, p in PROJECTS.items()]


@app.post("/api/projects/sample", response_model=ProjectDetail)
def create_sample_project():
    """Demo helper: create a project from the bundled sample without file upload."""
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
    pdf: UploadFile | None = File(None),
):
    """Create a project from an uploaded PDF."""
    if pdf is None:
        raise HTTPException(status_code=400, detail="PDF file is required")
    pdf_path = UPLOAD_DIR / f"{uuid.uuid4()}_{pdf.filename}"
    with open(pdf_path, "wb") as f:
        f.write(await pdf.read())
    return _create_project(pdf_path=pdf_path, name=name, units_per_variant={}, developer=developer)


def _create_project(
    pdf_path: Path,
    name: str,
    units_per_variant: dict[str, int],
    developer: str,
) -> ProjectDetail:
    """Internal: run the extraction pipeline + store the result."""
    pid = str(uuid.uuid4())[:8]

    # Auto-detect variants
    variants_meta = pdf_parser.identify_variants(pdf_path)

    # Default unit counts if not provided
    if not units_per_variant:
        units_per_variant = {code: 50 for _, code, _ in variants_meta}

    # Run pipeline
    result = run_extraction(
        pdf_path=pdf_path,
        template_path=SAMPLE_TEMPLATE,
        project_name=name,
        units_per_variant=units_per_variant,
        skip_recalc=True,
    )

    # Store
    PROJECTS[pid] = {
        "name": name,
        "developer": developer,
        "blueprint_pdf_path": str(pdf_path),
        "created_at": datetime.now().isoformat(),
        "status": "Awaiting review",
        "units_per_variant": units_per_variant,
        "approved": set(),
        "variants_meta": variants_meta,
        "extraction_result": result,
    }

    return _project_detail(pid)


def _project_detail(pid: str) -> ProjectDetail:
    if pid not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    p = PROJECTS[pid]
    summary = _to_summary(pid, p)
    variants = []
    for v in p["extraction_result"].project.variants:
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


@app.get("/api/projects/{pid}/variants/{code}", response_model=VariantDetail)
def get_variant(pid: str, code: str):
    if pid not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    p = PROJECTS[pid]
    for v in p["extraction_result"].project.variants:
        if v.type_code == code:
            rows_out = [_row_to_out(i, r) for i, r in enumerate(v.rows)]
            rules_fired = sorted({
                r.rule_citation.rule_id for r in v.rows
                if r.rule_citation
            })
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
            )
    raise HTTPException(status_code=404, detail=f"Variant {code} not found")


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
    return {"approved": body.approved, "project_status": p["status"]}


class RowUpdate(BaseModel):
    width_mm: int | None = None
    depth_mm: int | None = None
    height_mm: int | None = None
    code: str | None = None
    name: str | None = None


@app.patch("/api/projects/{pid}/variants/{code}/rows/{i}", response_model=CabinetRowOut)
def update_row(pid: str, code: str, i: int, update: RowUpdate):
    """Inline edit a row. Marks source=HUMAN."""
    if pid not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    p = PROJECTS[pid]
    for v in p["extraction_result"].project.variants:
        if v.type_code == code:
            if i < 0 or i >= len(v.rows):
                raise HTTPException(status_code=404, detail="Row not found")
            row = v.rows[i]
            if update.width_mm is not None:
                row.width_mm = update.width_mm
            if update.depth_mm is not None:
                row.depth_mm = update.depth_mm
            if update.height_mm is not None:
                row.height_mm = update.height_mm
            if update.code is not None:
                row.code = update.code
            if update.name is not None:
                row.name = update.name
            row.source = RowSource.HUMAN
            row.confidence = 1.0
            return _row_to_out(i, row)
    raise HTTPException(status_code=404, detail=f"Variant {code} not found")


@app.get("/api/projects/{pid}/blueprint/{page}.png")
def get_blueprint_page(pid: str, page: int, dpi: int = 150):
    """Render a PDF page as PNG for the blueprint canvas."""
    if pid not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    pdf_path = PROJECTS[pid]["blueprint_pdf_path"]
    img = pdf_parser.render_page(pdf_path, page, dpi=dpi)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@app.get("/api/rules")
def get_rules():
    """List the rule library (for reference / cell inspector)."""
    return list_rules()
