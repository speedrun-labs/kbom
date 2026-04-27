# KBOM — AI-assisted Kitchen BOM from Blueprints

Stage 1 prototype: NEFS pilot.

Walks an estimator from receiving a blueprint PDF to handing off an approved cabinet + install BOM, with the customer's existing Excel template doing the calculation work server-side.

## Quick start

```bash
# 1. Install deps
python3 -m pip install -r requirements.txt

# 2. Set Anthropic API key (for Claude vision)
export ANTHROPIC_API_KEY=sk-ant-...

# 3. Run the Streamlit app
streamlit run app/streamlit_app.py
```

## Project layout

```
kbom/                        Core pipeline (importable Python package)
  geometry/                  Path A: PDF parser (DXF adapter comes in Stage 2)
  vision/                    Claude vision wrapper for symbol classification
  rules/                     R1-R23 domain rules with LH catalog citations
  excel/                     Template populator + LibreOffice recalc + reader
  pipeline.py                Orchestrates extract → rules → write → recalc → read
  catalog/                   Developer profile: LH 표준상세도 V2025.01
  models.py                  Data classes (CabinetRow, ExtractedBOM, RuleCitation)

app/                         Streamlit UI
  streamlit_app.py           Entry point — project list
  pages/                     Sub-pages (Project Setup, Review, BOM)
  components/                Reusable UI components (cell inspector, etc.)

data/                        Sample blueprints + ground truth
phase0/                      Validation artifacts (read-only reference)
published_standards/         LH catalog PDFs + extracts
```

## What's working

- ✅ PDF text + line extraction (Test 1, Phase 0)
- ✅ Per-page variant detection
- ✅ Vision extraction via Claude (76% blind, 0 hallucinations)
- ✅ Rule engine R1–R23 (76% → 100% strict match after rules)
- ✅ Excel populator → 장등록 + 상품등록 + 기초입력
- ✅ LibreOffice headless recalc (0% round-trip variance)
- ⏳ Streamlit review UI (this prototype)
- ⏳ Project workspace + cell inspector (this prototype)

## What's not in this prototype

- Multi-tenant isolation (Stage 2)
- Diff engine for revisions (Stage 3)
- Purchasing integration (Stage 4)
- Mobile install app (Stage 5)
- Path B (PDF→DXF) and Path C (native DWG) adapters (Stage 2+)
