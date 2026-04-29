# KBOM — Kitchen BOM extraction from blueprints

> **AI pipeline + web app that turns construction-company blueprint PDFs into a populated Bill-of-Materials inside the customer's existing Excel template.**

Stage 1 pilot for [NEFS](https://www.nefs.co.kr/) — a Korean full-turnkey kitchen fabrication + install company that bids primarily on LH (Korea Land & Housing Corporation) public-housing projects.

The pipeline doesn't replace the customer's Excel — it **feeds it**. The customer's 18-tab Excel template (with 6,400+ rows of formulas, hardware rules, and cost rollups) keeps doing what it already does well. KBOM automates the manual *PDF → 21-input-rows transcription* step that today consumes ~6 person-years annually at NEFS.

---

## What it does

```
Blueprint PDF                                Customer's Excel template
┌─────────────────┐                          ┌──────────────────────┐
│   화성태안3      │                          │  18 tabs             │
│   A2BL          │  ─────KBOM──────────▶    │  ↓                   │
│   (LH detail)   │  vision + rules +        │  populated 장등록 +    │
│                 │  Excel populator         │  상품등록 + 기초입력  │
│   21 pages      │                          │  ↓                   │
│   7 variants    │                          │  6,400 cells of      │
│                 │                          │  formulas recompute  │
└─────────────────┘                          └──────────────────────┘
       │                                              │
       ▼                                              ▼
   Web UI for review                       Same .xlsx file the
   (project list, BOM grid,                regulator already audits
   provenance, ⌘K, etc.)
```

**Validated end-to-end on the supplied LH sample**:
- ✅ PDF parses cleanly — 21 pages, 7 unit-type variants auto-detected
- ✅ Vision extraction at **76%** strict match (Claude Opus 4.7 blind)
- ✅ After applying 8 catalog-cited rules → **100% strict match**
- ✅ Excel round-trip variance: **0% across 154,596 populated cells**

---

## Quick start

```bash
git clone https://github.com/speedrun-labs/kbom.git
cd kbom

./start-demo.sh        # auto-installs deps, boots both servers
# Open http://localhost:3737
```

The script:
- Creates `.venv/` (Python 3.12) and runs `pip install -r requirements.txt`
- Runs `npm install` in `web/` if needed
- Boots **FastAPI on `:8765`** and **Next.js on `:3737`**
- Health-checks both, prints URLs

Stop with `./stop-demo.sh`. Logs at `.logs/api.log` and `.logs/web.log`.

### Prerequisites

- Python **3.12+**
- Node **20+**
- LibreOffice (`brew install --cask libreoffice` on macOS) — for headless `.xls → .xlsx` conversion and Excel recalc

For live AI extraction (optional): set `ANTHROPIC_API_KEY`. Without it, KBOM uses a calibrated synthetic fallback (the same 26A sample BOM that Phase 0 validated).

---

## Demo walkthrough (~90 seconds, 12 beats)

Click **Use sample** on the home page to load the bundled `화성태안3 A2BL` project.

| # | Click / press | What happens |
|---:|---|---|
| 1 | **Use sample** | Sample project loads in ~1 sec |
| 2 | Click into the project | Review workspace opens, defaulting to first variant `26㎡ A형` |
| 3 | Bottom bar reads | "3/3 validations · ₩222,365,520 (120 × ₩1,853,046) · Approve variant" |
| 4 | **Hover row 9** (`찬넬렌지밑장 / CR / 600×570×550`) | Blue rectangle appears on the blueprint, **on the range area** |
| 5 | **Hover row 11** (`찬넬씽크밑장 / CS / 800×570×700`) | Rectangle slides right and lands **on the sink basin icon** |
| 6 | **Click row 9** | Inspector drawer slides in: `Rule R6 (DA-91-150 page 567): "Range-base height = 550mm (recessed hob)"` |
| 7 | **Press J / K** | Row selection moves; blueprint and inspector follow |
| 8 | **Click `800` width on row 11**, type `825`, Enter | Pill flips from `●95` to `✎ edited`, cost recalculates, persisted via PATCH |
| 9 | Click `37㎡ B형` tab | Workspace switches; cost rolls to `₩92.6M` (50 × `₩1.85M`) |
| 10 | Click **Approve variant** | Status updates, tab gets ✓ |
| 11 | Click **Download Excel** | Populated `.xlsx` downloads — formulas intact, opens in Excel |
| 12 | Press **⌘K** anywhere | Command palette: project search, quick actions |

---

## Architecture

```
┌───────────────────┐    HTTP/JSON     ┌────────────────────┐
│  Next.js 16       │ ───────────────▶ │  FastAPI :8765     │
│  (web/, :3737)    │                  │  (server/main.py)  │
│  - Tailwind 4     │                  │                    │
│  - TanStack Query │                  │  wraps kbom/       │
│  - Zustand        │                  │  ├─ geometry/      │
│  - cmdk (⌘K)      │                  │  ├─ vision/        │
│  - lucide         │                  │  ├─ rules/ (R1–R8) │
└───────────────────┘                  │  ├─ catalog/lh_…   │
                                       │  ├─ excel/         │
                                       │  └─ pipeline.py    │
                                       └────────────────────┘
                                                  │
                                                  ▼
                                       ┌────────────────────┐
                                       │  Customer's .xls   │
                                       │  template          │
                                       │  (장등록/상품등록/  │
                                       │   기초입력 inputs)  │
                                       │  + LibreOffice     │
                                       │  headless recalc   │
                                       └────────────────────┘
```

### Pipeline stages

1. **PDF parse** (`kbom/geometry/pdf_parser.py`) — text + dimension labels with positions, per-page variant detection (`26㎡ A형`, `37㎡ B형`, etc.), pixel-accurate segment positions from the dimension ladder.
2. **Vision extract** (`kbom/vision/claude_extractor.py`) — Claude Opus 4.7 vision API on rendered page crops (live mode) or calibrated synthetic output (fallback).
3. **Rule engine** (`kbom/rules/engine.py`) — R1–R8 deterministic corrections + completions: range-base height = 550mm, baseboard always 150×20×2400, end-panels at run boundaries, etc. Each rule cites a source document.
4. **Excel populate** (`kbom/excel/populator.py`) — auto-converts legacy `.xls` to `.xlsx` via headless LibreOffice; writes 장등록 (rows 4–18 cols B–F), 상품등록 (rows 8+ cols A,C), 기초입력 (TYPE + 세대수).
5. **Recalc** (`kbom/excel/recalc.py`) — re-saves the workbook through LibreOffice to trigger formula recalculation.
6. **Read** (`kbom/excel/reader.py`) — pulls computed values + formulas back; serves to UI via API.

### Key invariants

- **Excel = source of truth for math.** Regulators audit the `.xlsx` directly. Same workflow they've used for 20 years.
- **DB = source of truth for provenance.** Who entered what, when, with what AI confidence, which rule version.
- **The customer's existing template is unchanged.** We populate inputs; their formulas do the rest.

---

## Project layout

```
kbom/                  Core pipeline (Python package)
├── geometry/          PDF parser + variant detection + segment extraction
├── vision/            Claude vision wrapper (live + synthetic)
├── rules/             R1–R8 with document citations
├── catalog/           LH developer profile (cabinet codes, products)
├── excel/             Populator + LibreOffice recalc + reader
├── pipeline.py        End-to-end orchestrator
└── models.py          CabinetRow, RuleCitation, CabinetSegment, etc.

server/main.py         FastAPI service wrapping the pipeline

web/                   Next.js 16 frontend
├── app/               Project list (/) + review workspace (/projects/[id])
├── components/
│   ├── review/        BlueprintCanvas, BomGrid, EditableCell, Inspector,
│   │                  ValidationsBar, VariantTabs, ConfidencePill
│   ├── projects/      NewProjectDialog (PDF upload)
│   ├── layout/        TopBar, LeftRail
│   ├── ui/            shadcn-style primitives (button, badge, card, dialog)
│   └── CommandPalette.tsx     ⌘K palette
├── lib/               api.ts (typed client), types.ts, store.ts (Zustand)
└── package.json       Next.js 16, React 19, Tailwind 4

phase0/                Validation artifacts (preserved as audit trail)
published_standards/   LH catalog mining report (committed)
                       Source PDFs are gitignored due to size

CLAUDE.md              Canonical project context (auto-loaded by Claude Code)
start-demo.sh          One-command demo launcher
stop-demo.sh           Kills both servers
requirements.txt       Python deps
```

---

## What's NOT in Stage 1

This is a working pilot prototype, not a production multi-tenant SaaS. Per the [approved roadmap](#roadmap), the following are deferred:

- Multi-tenant isolation, login, RBAC, full action log
- Immutable per-approval snapshots in versioned object storage
- Diff engine for blueprint revisions (v1 → v2)
- Purchasing integration (supplier registry, PO generation, ERP push)
- Mobile install app + as-built capture
- Path B (PDF→DXF) and Path C (native DWG) geometry adapters
- Real Excel recalc inside the request path (current cost calc is heuristic; recalc machinery exists but isn't wired into the cost endpoint to avoid 5–30s latency)
- R9–R23 rule implementations (catalog-cited but stubbed)

---

## Roadmap

| Stage | Scope | Personas entrenched |
|---|---|---|
| **A. Extraction** *(this prototype)* | Blueprint → cabinet + install BOM | Estimators |
| **B. Project workspace** | Project mgmt, revisions, rollup, RBAC | + Project managers |
| **C. Purchasing** | BOM → supplier SKU + lead time + stock → PO generation → ERP push | + Purchase team |
| **D. Fabrication** | BOM → cut lists, CNC files, panel optimizer, production schedule | + Production planners |
| **E. Install** | Install BOM → mobile app + as-built capture + photo evidence | + Install leads |
| **F+G. Cross-project** | Portfolio dashboards, win-rate analytics, bid-pricing AI | + Executives |

Decision gates at each stage boundary. See the strategy doc (private) for stage-gate ARR targets, hiring plan, and decision criteria.

---

## Validation evidence

| Test | Result | Source |
|---|---|---|
| PDF vector parsing | **PASS** — 338 dim / 486 spec / 136 view / 84 title-block hits across 21 pages | [phase0/report.md](phase0/report.md) |
| Ground truth extraction | 21 canonical rows (15 목대 + 6 상품) from sample Excel | [phase0/ground_truth_26A.json](phase0/ground_truth_26A.json) |
| Blind vision extraction | **76% coverage**, 52% strict match, 0 hallucinations | [phase0/report.md](phase0/report.md) |
| After R1–R8 rules applied | **100% strict match** on all 21 ground-truth rows | [phase0/report_extension.md](phase0/report_extension.md) |
| Cross-variant robustness | Same rules apply unchanged to 26A1 + 37B (different geometry, different sink size) | [phase0/predictions_37B.json](phase0/predictions_37B.json) |
| Excel round-trip | **0% variance** across 154,596 populated cells | (round-trip script in `phase0/roundtrip/`) |
| Standards mining | 23 catalog-cited rules from LH 표준상세도 V2025.01 | [published_standards/standards_mining_report.md](published_standards/standards_mining_report.md) |

---

## Sample artifacts

The validated sample (used in Phase 0 testing and demo):

- **PDF**: `붙임3-2. 주방가구 상세도(화성태안3 A-2BL)-2.pdf` (21 pages, 7 variants)
- **Excel template**: `1. LH 화성태안3 A2BL-26A.xls` (18 tabs, ~26MB)

These are NEFS-supplied artifacts and are not committed. Place them at `~/Downloads/` to use the sample-loader. The pipeline accepts any LH-style blueprint PDF + any compatible 18-tab Excel template.

---

## Troubleshooting

```bash
# Tail logs
tail -f .logs/api.log .logs/web.log

# Reset state
rm .kbom-state.json && ./stop-demo.sh && ./start-demo.sh

# Verify ports free
lsof -i:8765 -i:3737
```

| Symptom | Fix |
|---|---|
| `http://localhost:3737` doesn't load | `./stop-demo.sh && ./start-demo.sh`; wait for ✓ |
| Servers fail to start | `tail -20 .logs/api.log` and `.logs/web.log`; usually port `8765` or `3737` is taken |
| Excel download is empty/broken | LibreOffice not installed: `brew install --cask libreoffice` |
| "No variants detected" on upload | The PDF isn't a vector PDF (might be scanned). Use the bundled sample. |
| Want to start fresh | `rm .kbom-state.json && ./stop-demo.sh && ./start-demo.sh` |

---

## License

[MIT](LICENSE)

---

*Built by [speedrun-labs](https://github.com/speedrun-labs).*
