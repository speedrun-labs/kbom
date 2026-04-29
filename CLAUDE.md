# CLAUDE.md — KBOM project context

This file is auto-loaded by Claude Code when working in this directory.
Read this first in any new session before proposing changes.

---

## What this is

**KBOM** (Kitchen BOM) — an AI pipeline + web app that turns construction-company
blueprint PDFs into a populated kitchen Bill-of-Materials inside the customer's
existing Excel template. Stage 1 pilot is for **NEFS**, a Korean full-turnkey
kitchen fabrication + install company that bids primarily on LH (Korea Land &
Housing Corporation) public-housing projects.

**Why it exists**: 6 NEFS FTEs spend their time manually reading blueprint PDFs
and itemizing cabinets into Excel. 3–4 major blueprint revisions per project,
each historically a from-scratch redo. Install-side rules (2x4s, outlets,
plumbing offsets) aren't written down anywhere. Delays cascade into the
purchase team, which is the primary downstream consumer of the BOM today.

**Primary user**: NEFS purchase team. Tool is a *purchasing decision engine*,
not just a BOM producer. Output optimizes for pre-ordering against tight
construction schedules.

**Mental model**: We don't replace the customer's Excel template — that
already does the math. We **feed it** by automating the manual PDF →
21-input-rows transcription step that today consumes 6 person-years annually.

---

## The user (Darren / darren@hgvp.xyz)

- Strategic / product lead at NEFS, **non-Korean-speaking**.
- Treat all responses **English-first**. Korean terms (sheet names, cabinet
  types, finish specs) get an English gloss inline:
  `원가산출표 (cost calculation sheet)`, `목대 (custom frame parts)`,
  `찬넬렌지밑장 (channel-mount range base)`. Never leave a Korean term unglossed.
- Wants **concrete walkthroughs** over abstract explanation. When asked
  "how does X work?", anchor the answer to a specific row / specific
  blueprint / specific transformation, not a hand-wavy mechanism.
- Asks pointed business questions ("how does this help current workflow?",
  "how is this scalable?", "do we need this instead of Excel?"). Answer
  directly with numbers and trade-offs; honest about what's NOT solved.
- Catches sleight-of-hand fast. Don't oversell. Diagnose, fix, ship.

---

## How to run the demo

```bash
cd "/Users/d/Desktop/NEFS Kitchen"
./start-demo.sh        # boots FastAPI + Next.js, prints URLs
# Open http://localhost:3737
./stop-demo.sh         # when done
```

The script:
- Auto-creates Python `.venv/` (Python 3.12 required) with FastAPI + kbom deps
- Auto-runs `npm install` in `web/` if `node_modules/` missing
- Starts FastAPI on `:8765`, Next.js on `:3737`
- Health-checks both, prints URLs, leaves them running
- Logs at `.logs/api.log` and `.logs/web.log`

Demo flow (90 seconds): see [README.md](./README.md).

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
│  - PDF rendered   │                  │  ├─ catalog/lh_…   │
│    server-side    │                  │  ├─ excel/         │
│    via API        │                  │  └─ pipeline.py    │
└───────────────────┘                  └────────────────────┘
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

Two invariants:
- **Excel = source of truth for math** (regulators audit the .xlsx file directly)
- **Postgres/JSON = source of truth for provenance** (who entered what, when, with what AI confidence)

**Persistence**: `.kbom-state.json` at project root. Project metadata + row
overrides + approvals survive restart. Extraction results are RAM-only and
re-run on demand from the source PDF.

---

## File layout

```
NEFS Kitchen/
├── CLAUDE.md              ← THIS FILE — read first in any new session
├── README.md              ← User-facing demo + architecture (public)
├── LICENSE                ← MIT
├── start-demo.sh          ← Boot both servers
├── stop-demo.sh           ← Kill them
├── requirements.txt       ← Python deps (FastAPI + kbom pipeline)
│
├── kbom/                  ← Core pipeline (Python, importable package)
│   ├── models.py          CabinetRow, RuleCitation, CabinetSegment, Project
│   ├── geometry/
│   │   └── pdf_parser.py  Path A: PDF parser, variant detection, segment extraction
│   ├── vision/
│   │   └── claude_extractor.py Live Claude API + synthetic fallback
│   ├── rules/
│   │   └── engine.py      R1–R8 implemented (R9–R23 documented in standards report)
│   ├── catalog/
│   │   └── lh_v2025.py    LH cabinet vocabulary + standard products
│   ├── excel/
│   │   ├── populator.py   Write 장등록 + 상품등록 + 기초입력 (auto .xls→.xlsx)
│   │   ├── recalc.py      LibreOffice headless recalc
│   │   └── reader.py      Read computed values + formulas
│   └── pipeline.py        Orchestrate extract → rules → write → recalc → read
│
├── server/main.py         ← FastAPI wrapping kbom (REST API on :8765)
│
├── web/                   ← Next.js 16 frontend
│   ├── app/
│   │   ├── page.tsx                     project list (/)
│   │   ├── projects/[id]/page.tsx       review workspace
│   │   ├── layout.tsx                   root layout + QueryProvider + CommandPalette
│   │   └── globals.css                  Tailwind 4 theme
│   ├── components/
│   │   ├── layout/{TopBar,LeftRail}.tsx
│   │   ├── projects/NewProjectDialog.tsx  Upload PDF + create project
│   │   ├── review/
│   │   │   ├── ReviewWorkspace.tsx      3-pane main view
│   │   │   ├── BlueprintCanvas.tsx      Rendered PDF + SVG segment overlay
│   │   │   ├── BomGrid.tsx              Extracted-rows table with J/K nav
│   │   │   ├── EditableCell.tsx         Click W/D/H → input → PATCH
│   │   │   ├── Inspector.tsx            Right-side drawer with provenance
│   │   │   ├── ValidationsBar.tsx       Bottom bar: cost, approve, download
│   │   │   ├── VariantTabs.tsx          Tabs across unit-type variants
│   │   │   └── ConfidencePill.tsx       Green/yellow/red/rule/spec badges
│   │   ├── ui/                          shadcn-style primitives
│   │   ├── providers/QueryProvider.tsx  TanStack Query
│   │   └── CommandPalette.tsx           ⌘K palette
│   ├── lib/
│   │   ├── api.ts                       Typed API client
│   │   ├── types.ts                     Mirrors pydantic models
│   │   ├── store.ts                     Zustand UI state
│   │   └── utils.ts                     cn() + KRW formatter
│   └── package.json                     Next.js 16, React 19, Tailwind 4
│
├── phase0/                ← Validation artifacts
│   ├── domain_rules.py    First-iteration rules (since ported into kbom/rules/)
│   ├── ground_truth_26A.json  21-row canonical BOM from sample Excel
│   ├── report.md          Validation report (Tests 1–3)
│   └── report_extension.md  Cross-variant + rules-proof
│
├── published_standards/   ← LH catalog mining (committed: report only)
│   └── standards_mining_report.md  ← 23-rule library with citations
│
├── .venv/                 ← Python venv (gitignored)
├── .logs/                 ← Demo logs (gitignored)
├── .kbom-state.json       ← Persisted project state (gitignored)
└── .runs/, .uploads/      ← Runtime files (gitignored)
```

---

## What's working (Stage 1 — demo-ready)

- ✅ PDF variant detection (7 unit-type variants in the bundled sample)
- ✅ Pixel-accurate segment extraction from PDF dimension ladders (replaces hardcoded coords)
- ✅ Vision extraction (synthetic fallback for fast demo without API costs)
- ✅ Rule engine R1–R8 (proven 76% → 100% strict match on the sample)
- ✅ Excel populator (writes 장등록 + 상품등록 + 기초입력; auto .xls → .xlsx)
- ✅ LibreOffice headless recalc (proven 0% variance round-trip)
- ✅ JSON-file persistence (`.kbom-state.json` survives restart)
- ✅ Real PDF upload (multipart → extraction → routes to project)
- ✅ Real cost computation (per-row heuristic + 30% labor markup)
- ✅ Inline cell editing (click W/D/H → PATCH → source flips to "human")
- ✅ **Blueprint↔row coordination** (hover/select row → SVG rect on PDF, pixel-accurate)
- ✅ Cell inspector with full provenance (formula + AI confidence + rule citation)
- ✅ ⌘K command palette (project search + actions)
- ✅ Excel download endpoint (returns the populated workbook)
- ✅ Variant tabs with flagged-count badges and approval ✓
- ✅ Validations bar with cost preview + approve mutation

## What's NOT in Stage 1 (deferred per the approved roadmap)

- ⏳ Multi-tenant isolation, RBAC, full action log (Stage 2)
- ⏳ Immutable per-approval snapshots in versioned object storage (Stage 2)
- ⏳ Diff engine for blueprint revisions v1→v2 (Stage 3)
- ⏳ Purchasing integration — supplier registry, PO generation, ERP push (Stage 4)
- ⏳ Mobile install app + as-built capture (Stage 5)
- ⏳ Path B (PDF→DXF) and Path C (native DWG) geometry adapters (Stage 2+)
- ⏳ Real LibreOffice recalc inside the request path (recalc machinery is built;
  cost endpoint currently uses heuristic to avoid 5–30s latency)
- ⏳ R9–R23 rule implementations (catalog-cited but stubbed)
- ⏳ Cell-inspector "Open in Excel" button (data path is built; needs Excel deep-link)

---

## Critical context: how the Excel template works

NEFS's 18-tab Excel is a **calculation engine**, not a document.

**Real data inputs** (write here):
1. `장등록(규격,수량,옵션)` — cabinet rows (15 목대 for 26A)
   - Rows 4–18, cols B (code), C (name), D (W), E (D), F (H)
2. `상품등록` — product rows (6 상품 for 26A)
   - Rows 8–13, col A (key as `상품{name}`) + col C (name)
3. `기초입력(사양등록)` — project assumptions
   - C4 = TYPE (e.g. "26A"), C5 = 세대수

**Computed views** (DO NOT write here — they're VLOOKUP/OFFSET formulas):
- `원가산출표` (the "cabinet list" — actually a *view* of `장등록` + `상품등록`)
- `자재구성표(BODY/DOOR)` — material breakdown
- `BOM구성표` — hardware counts (via `DATA(철물구성)` rules)
- `일위대가표` — cost rollup (6,400+ rows of formulas)

**Cabinet code system in 장등록**: `WP, W, BI, C, CR, CD3, CS, BP, FA, PL`.
This differs from `DATA(철물구성)` codes (`B, BR, BS, BD3` without 찬넬 prefix).
The two coexist; 장등록 rows reference 철물구성 rules through internal mapping.

**Row order matters in 장등록** — per-row computations cascade. Convention:
wall-cab assembly first (panels + cabs), then 밑장휠라, then base run
(plain → range → drawer → sink), then BP/FA/PL trim.

**Exact-value sensitivity**: 1mm differences propagate. Excel uses
`찬넬렌지밑장 W=601` (engineered for hob-recess clearance); blueprint shows
`600`. Pipeline should fetch dimensions from 장등록 catalog where possible,
not blindly trust dimension-ladder labels.

---

## The 23-rule library

Living in [published_standards/standards_mining_report.md](./published_standards/standards_mining_report.md).
R1–R8 implemented in [kbom/rules/engine.py](./kbom/rules/engine.py).
R9–R23 documented but stubbed.

| Group | Rules | Source |
|---|---|---|
| **R1–R8** | Round-trip-derived: outer panels 860H, base end panel, base filler, fascia/baseboard 2400 stock, range-base 550H, panel dim swap, accessory catalog | NEFS Excel round-trip (Phase 0) |
| **R9–R16** | Cabinet-side: countertop seamless ≤ 2400, drawer rail clearance, lighting scope, pull-out basket hangers | LH 표준상세도 V2025.01, DA-91-1xx pages |
| **R17–R23** | Install-side: baseboard 150H + 60mm offset, flooring/paint don't extend behind cabinets, wall-tile 100mm reveal, upper-cab ceiling gap max 25mm | LH 표준상세도, DA-91-150 to 155 |

Every rule has a **document citation** (LH catalog page or round-trip
reference). The cell inspector surfaces these — click any row, see why it
exists.

---

## Communication style for any future session with Darren

1. **English first**, gloss every Korean term inline.
2. **Concrete over abstract** — "for the sink base in your sample, here's
   what happens" beats "in general the pipeline does X."
3. **Honest about what's NOT solved** — Darren caught the SVG sizing bug
   immediately and pushed back when I oversold the hotfix. He doesn't
   tolerate sleight-of-hand. Diagnose, fix, ship.
4. **Numbers when possible** — "76% → 100% after rules", "₩222.4M total",
   "0% variance across 154,596 cells". Avoid vague claims.
5. **Frame against Excel-alone, not against nothing**. The customer already
   has Excel; KBOM's value is what it adds beyond Excel-alone.

---

## Productization context (for Stage 2+ conversations)

The plan file (`/Users/d/.claude/plans/users-d-downloads-1-lh-3-a2bl-26a-xls-peaceful-sun.md`)
captures the full productization roadmap. Key decisions locked in:

- **Demand-driven developer onboarding**: don't pre-build LH/SH/GH/private
  developer profiles speculatively. When a paying customer asks for SH,
  add it in 1 week. Engineering investment goes into the *onboarding tool*.
- **Phase C (Purchasing) ships first** after project workspace. Validated
  by NEFS purchase team being the primary persona. Highest immediate ROI.
- **Tenant-private rules, never shared**. Strongest data-privacy stance.
  Primary moat is workflow lock-in via value-chain integration (A→B→C→D→E),
  not cross-tenant data network effects.
- **Web app for users; Excel runs server-side as the calc engine.** Users
  never see Excel. The customer's existing template is the audit artifact
  (regulators open it directly). Two audit paths: math (Excel) +
  provenance (platform DB metadata).

---

## Known issues / things that need follow-up

- **Cost calculation is heuristic.** ~₩250k/m² of cabinet frontage + product
  flat rates + 30% labor markup. Final number should come from the actual
  Excel recalc through 일위대가표 — the recalc machinery is built but not
  wired into the cost endpoint (would add 5–30s to the request).
- **Synthetic vision mode** returns the 26A sample BOM regardless of the
  uploaded PDF. To get real extraction, set `ANTHROPIC_API_KEY` env var
  (the live path in `kbom/vision/claude_extractor.py` is wired but commented).
- **Single-tenant**. Login, RBAC, action log are Stage 2 work.
- **Segment extraction y-bounds use a heuristic** (50pt below dim labels,
  120pt span). Pixel-accurate horizontally; vertically approximate. Path B
  (DXF) gives exact polygon coordinates and is the proper long-term fix.
- **Synthetic mode masks variant differences.** All 7 variants currently show
  the same 26A BOM in synthetic mode. Live API mode would extract per-variant
  rows. For demo purposes, synthetic is fast + free + deterministic.

---

## Quick reference

```bash
# Demo
./start-demo.sh
./stop-demo.sh

# Logs
tail -f .logs/api.log .logs/web.log

# Reset state
rm .kbom-state.json && ./stop-demo.sh && ./start-demo.sh

# Direct API smoke test
curl -sS http://localhost:8765/api/health
curl -sS -X POST http://localhost:8765/api/projects/sample
curl -sS http://localhost:8765/api/projects

# Frontend dev (auto-reloads on save)
cd web && npm run dev -- --port 3737

# Backend dev (auto-reloads on save)
.venv/bin/python -m uvicorn server.main:app --port 8765 --reload
```

**Sample artifacts** (the real LH project we've been validating against):
- PDF: `/Users/d/Downloads/붙임3-2. 주방가구 상세도(화성태안3 A-2BL)-2.pdf` (21 pages, 7 variants)
- Excel template: `/Users/d/Downloads/1. LH 화성태안3 A2BL-26A.xls` (18 tabs, 26MB)

**Plan file** (the strategic doc with the full productization roadmap):
`/Users/d/.claude/plans/users-d-downloads-1-lh-3-a2bl-26a-xls-peaceful-sun.md`

**Repo**: https://github.com/speedrun-labs/kbom

---

*Last updated: 2026-04-28 — Stage 1 prototype demo-ready, pixel-accurate segments shipped.*
