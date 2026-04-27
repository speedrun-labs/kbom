# KBOM — Kitchen BOM extraction from blueprints

AI pipeline + web UI that turns construction-company blueprint PDFs into a
populated kitchen Bill-of-Materials inside the customer's existing Excel
template — for the NEFS Stage 1 pilot.

## Run the demo

```bash
./start-demo.sh

# Then open http://localhost:3737
```

The script boots:
- **FastAPI** on `:8765` — wraps the `kbom` Python pipeline as a REST API
- **Next.js** on `:3737` — frontend (project list, review workspace, cell inspector)

Click **"Use sample"** to load the bundled `화성태안3 A2BL` (7 unit-type variants,
400 units, 21-row BOM per variant). Or click **+ New project** to upload your
own PDF.

Stop with `./stop-demo.sh`. Logs in `.logs/api.log` and `.logs/web.log`.

## What the demo shows

**Project list** — recent projects with developer badge, variants, approval
status. ⌘K opens a command palette for fast nav.

**Review workspace** for each project — three coordinated panes:

1. **Blueprint canvas** (left): rendered PDF page with zoom controls. Hover or
   select a row in the BOM grid → a colored rectangle highlights the
   corresponding cabinet on the blueprint. Click a segment → row selects.

2. **BOM grid** (middle): every extracted cabinet/product. Confidence pills
   (green/yellow/red for vision; rule/catalog/spec/edited badges for derived
   rows). Each rule-fired row carries its citation (R1–R8 → LH 표준상세도
   page reference). **Click any W/D/H number to edit it inline** — Enter saves
   via the API. **J/K** to navigate rows.

3. **Inspector** (right, drawer): provenance for the selected row — source
   sheet/cell, type label, AI confidence, rule citation with document and
   section code. Drawer toggles open when you select a row.

**Bottom bar**: validations summary, real cost estimate, **Download Excel**
(populated workbook with the customer's formulas), **Approve variant**.

## Architecture

```
┌──────────────────┐         HTTP/JSON          ┌────────────────────┐
│  Next.js 16      │ ─────────────────────────▶ │  FastAPI :8765     │
│  (web/, :3737)   │                            │  (server/main.py)  │
│  - Tailwind 4    │                            │                    │
│  - TanStack      │                            │  wraps kbom/       │
│  - Zustand       │                            │  ├─ geometry/      │
│  - cmdk          │                            │  ├─ vision/        │
│  - lucide        │                            │  ├─ rules/ (R1-R8) │
└──────────────────┘                            │  ├─ catalog/lh_…   │
                                                │  ├─ excel/         │
                                                │  └─ pipeline.py    │
                                                └────────────────────┘
                                                          │
                                                          ▼
                                                ┌────────────────────┐
                                                │  Customer's .xls   │
                                                │  template          │
                                                │  (장등록/상품등록/ │
                                                │   기초입력 inputs) │
                                                │  + LibreOffice     │
                                                │  headless recalc   │
                                                └────────────────────┘
```

Persistence: `.kbom-state.json` (project metadata + row overrides survive
restart). Extraction results re-run on demand from the source PDF.

## Project layout

```
NEFS Kitchen/
├── start-demo.sh / stop-demo.sh  ← demo launcher
├── kbom/                         ← Python pipeline
│   ├── geometry/pdf_parser.py    Path A: PDF parser, variant detection
│   ├── vision/claude_extractor.py Claude vision (or synthetic fallback)
│   ├── rules/engine.py           R1–R8 with citations
│   ├── catalog/lh_v2025.py       LH developer profile
│   ├── excel/populator.py        Write 장등록 / 상품등록 / 기초입력
│   ├── excel/recalc.py           LibreOffice headless recalc
│   ├── excel/reader.py           Read computed values + formulas
│   └── pipeline.py               Orchestrator
├── server/main.py                FastAPI wrapper
├── web/                          Next.js 16 frontend
│   ├── app/page.tsx              project list (/)
│   ├── app/projects/[id]/page.tsx review workspace
│   └── components/
│       ├── layout/{TopBar,LeftRail}.tsx
│       ├── projects/NewProjectDialog.tsx
│       ├── review/{ReviewWorkspace,BlueprintCanvas,BomGrid,EditableCell,Inspector,ValidationsBar,VariantTabs,ConfidencePill}.tsx
│       ├── ui/{button,badge,card,dialog}.tsx
│       └── CommandPalette.tsx
├── phase0/                       Validation artifacts (Phase 0)
└── published_standards/          LH catalog mining report
```

## Key flows

### Inline edit
Click any W/D/H number in the BOM grid → input field. Enter to save (PATCHes
`/api/projects/{id}/variants/{code}/rows/{i}`); Esc to cancel. The row's source
flips to `human` and the override persists across restart.

### Row selection ↔ blueprint highlight
Hover a row → blueprint segment lights up at ~10% opacity. Click → selects
(20% opacity + border, inspector opens). Click a blueprint segment → row
selects in the grid.

### Approve & download
Click **Approve variant** in the bottom bar. Status updates. Click **Download
Excel** to get the populated workbook (legacy `.xls` template auto-converted
to `.xlsx`, formulas intact).

### Cmd+K
Search projects, jump straight to the review workspace, create sample.

## What's NOT in this demo (Stage 2+ scope)

- Multi-tenant / auth (single-user prototype)
- Diff engine for blueprint revisions (v1 → v2)
- Purchasing integration (supplier registry, PO generation, ERP push)
- Mobile install app + as-built capture
- DXF / native DWG geometry adapters (Path B/C)
- Real-time multi-user editing
- LibreOffice recalc inside the request path (cost is heuristic per-unit; full
  recalc is a separate `POST .../recalc` endpoint, not yet wired into the UI)

## Troubleshooting

```bash
# Tail logs
tail -f .logs/api.log .logs/web.log

# Force-reset state
rm .kbom-state.json
./stop-demo.sh && ./start-demo.sh

# Verify ports free
lsof -i:8765 -i:3737
```

LibreOffice (soffice) must be installed for `.xls` template conversion and
recalc. macOS: `brew install --cask libreoffice`.
