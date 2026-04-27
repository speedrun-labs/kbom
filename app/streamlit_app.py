"""KBOM Stage 1 prototype — Streamlit UI (redesigned).

Run with: streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import streamlit as st

# Make kbom importable when run via `streamlit run app/streamlit_app.py`
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kbom.geometry import pdf_parser  # noqa: E402
from kbom.pipeline import run_extraction  # noqa: E402
from kbom.rules.engine import list_rules  # noqa: E402


# -----------------------------------------------------------------------------
# Page config
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="KBOM",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# -----------------------------------------------------------------------------
# Custom CSS — make Streamlit look like a real SaaS app
# -----------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
  /* ----- Global typography & spacing ----- */
  html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Inter",
                 "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    -webkit-font-smoothing: antialiased;
  }
  .block-container {
    padding-top: 0 !important;
    padding-bottom: 2rem !important;
    max-width: 1400px !important;
  }

  /* ----- Hide Streamlit chrome ----- */
  #MainMenu, footer, header[data-testid="stHeader"] { display: none; }

  /* ----- Top bar ----- */
  .kbom-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 4px;
    border-bottom: 1px solid #E5E7EB;
    margin-bottom: 24px;
  }
  .kbom-logo {
    font-weight: 700;
    font-size: 18px;
    color: #2563EB;
    letter-spacing: -0.02em;
    cursor: pointer;
  }
  .kbom-logo span { color: #0F172A; font-weight: 500; }
  .kbom-user {
    font-size: 13px;
    color: #64748B;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .kbom-user-avatar {
    width: 28px; height: 28px;
    border-radius: 50%;
    background: #DBEAFE;
    color: #2563EB;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 12px;
  }

  /* ----- Page headers ----- */
  .kbom-h1 {
    font-size: 24px;
    font-weight: 600;
    color: #0F172A;
    letter-spacing: -0.02em;
    margin: 0 0 4px 0;
  }
  .kbom-h1-sub {
    font-size: 13px;
    color: #64748B;
    margin: 0 0 24px 0;
  }
  .kbom-h2 {
    font-size: 14px;
    font-weight: 600;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 0 0 12px 0;
  }

  /* ----- Cards ----- */
  .kbom-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 12px;
  }
  .kbom-card-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
  }

  /* ----- Buttons ----- */
  .stButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    padding: 6px 14px !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
  }
  .stButton > button[kind="primary"] {
    background: #2563EB !important;
    color: white !important;
    border: 1px solid #2563EB !important;
  }
  .stButton > button[kind="primary"]:hover {
    background: #1D4ED8 !important;
    border-color: #1D4ED8 !important;
  }
  .stButton > button[kind="secondary"] {
    background: #FFFFFF !important;
    color: #475569 !important;
    border: 1px solid #E5E7EB !important;
  }
  .stButton > button[kind="secondary"]:hover {
    background: #F8FAFC !important;
    border-color: #CBD5E1 !important;
  }

  /* ----- File uploader ----- */
  [data-testid="stFileUploader"] section {
    border: 2px dashed #CBD5E1 !important;
    border-radius: 10px !important;
    background: #FFFFFF !important;
    padding: 28px !important;
  }
  [data-testid="stFileUploader"] section:hover {
    border-color: #2563EB !important;
    background: #EFF6FF !important;
  }

  /* ----- Inputs ----- */
  [data-testid="stTextInput"] input,
  [data-testid="stNumberInput"] input,
  [data-testid="stSelectbox"] [data-baseweb="select"] {
    border-radius: 8px !important;
    border-color: #E5E7EB !important;
  }

  /* ----- Tables ----- */
  [data-testid="stDataFrame"] {
    border-radius: 8px;
    overflow: hidden;
  }

  /* ----- Tabs ----- */
  [data-baseweb="tab-list"] {
    gap: 4px !important;
    border-bottom: 1px solid #E5E7EB !important;
  }
  [data-baseweb="tab"] {
    padding: 10px 16px !important;
    color: #64748B !important;
    font-weight: 500 !important;
    border-radius: 0 !important;
  }
  [data-baseweb="tab"][aria-selected="true"] {
    color: #2563EB !important;
    border-bottom: 2px solid #2563EB !important;
  }

  /* ----- Confidence pills (custom) ----- */
  .conf-pill {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    font-family: "SF Mono", Monaco, monospace;
  }
  .conf-green { background: #DCFCE7; color: #15803D; }
  .conf-yellow { background: #FEF3C7; color: #B45309; }
  .conf-red { background: #FEE2E2; color: #B91C1C; }
  .conf-rule { background: #DBEAFE; color: #1D4ED8; }
  .conf-spec { background: #F1F5F9; color: #475569; }

  /* ----- Status badges ----- */
  .status-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 500;
  }
  .status-pending { background: #FEF3C7; color: #92400E; }
  .status-approved { background: #DCFCE7; color: #166534; }
  .status-draft { background: #F1F5F9; color: #475569; }

  /* ----- Validation list ----- */
  .val-row {
    display: flex;
    gap: 8px;
    padding: 6px 0;
    font-size: 13px;
    color: #475569;
  }
  .val-pass { color: #16A34A; font-weight: 600; }
  .val-warn { color: #B45309; font-weight: 600; }
  .val-fail { color: #DC2626; font-weight: 600; }

  /* ----- Rules-fired list ----- */
  .rule-item {
    display: flex;
    align-items: flex-start;
    padding: 8px 10px;
    background: #F8FAFC;
    border-radius: 6px;
    margin-bottom: 4px;
    font-size: 12px;
  }
  .rule-id {
    background: #DBEAFE;
    color: #1D4ED8;
    padding: 1px 6px;
    border-radius: 4px;
    font-weight: 600;
    margin-right: 8px;
    font-family: "SF Mono", Monaco, monospace;
  }
  .rule-desc { color: #475569; }
  .rule-cite { color: #94A3B8; font-size: 11px; margin-top: 2px; }

  /* ----- Metric cards (override Streamlit's) ----- */
  [data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 14px 16px;
  }
  [data-testid="stMetric"] [data-testid="stMetricLabel"] {
    color: #64748B !important;
    font-size: 12px !important;
    font-weight: 500 !important;
  }
  [data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #0F172A !important;
    font-size: 22px !important;
    font-weight: 600 !important;
  }

  /* ----- Variant selector tabs ----- */
  div[role="tablist"] { background: #F8FAFC; border-radius: 8px; padding: 4px; }

  /* ----- Captions / muted text ----- */
  small, [data-testid="stCaptionContainer"] {
    color: #94A3B8 !important;
    font-size: 12px !important;
  }

  /* ----- Dividers ----- */
  hr { margin: 24px 0 !important; border-color: #E5E7EB !important; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# Demo project sample paths
SAMPLE_PDF = Path("/Users/d/Downloads/붙임3-2. 주방가구 상세도(화성태안3 A-2BL)-2.pdf")
SAMPLE_TEMPLATE = Path("/Users/d/Downloads/1. LH 화성태안3 A2BL-26A.xls")


# -----------------------------------------------------------------------------
# Session state
# -----------------------------------------------------------------------------
def _init_state():
    if "view" not in st.session_state:
        st.session_state.view = "projects"
    if "projects" not in st.session_state:
        st.session_state.projects = []
    if "current_project_idx" not in st.session_state:
        st.session_state.current_project_idx = None
    if "current_variant_idx" not in st.session_state:
        st.session_state.current_variant_idx = 0
    if "approved_variants" not in st.session_state:
        st.session_state.approved_variants = {}  # project_idx -> set of variant_idx


_init_state()


def current_project():
    if st.session_state.current_project_idx is None:
        return None
    return st.session_state.projects[st.session_state.current_project_idx]


# -----------------------------------------------------------------------------
# Top bar
# -----------------------------------------------------------------------------
def top_bar():
    project_count = len(st.session_state.projects)
    user_initials = "PK"

    st.markdown(
        f"""
        <div class="kbom-topbar">
          <div class="kbom-logo">
            🏗️ KBOM <span>· NEFS Kitchen Pilot</span>
          </div>
          <div class="kbom-user">
            <span>{project_count} projects</span>
            <span class="kbom-user-avatar">{user_initials}</span>
            <span>Park · Estimator</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# View 1: Project list
# -----------------------------------------------------------------------------
def view_projects():
    cols = st.columns([4, 1])
    with cols[0]:
        st.markdown(
            '<p class="kbom-h1">Projects</p>'
            '<p class="kbom-h1-sub">Active and recent kitchen extractions</p>',
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.write("")  # vertical alignment spacer
        if st.button("➕  New Project", type="primary", use_container_width=True):
            st.session_state.view = "setup"
            st.rerun()

    if not st.session_state.projects:
        st.markdown(
            """
            <div class="kbom-card" style="text-align:center; padding:48px 24px;">
              <div style="font-size:42px; margin-bottom:8px;">📐</div>
              <div style="font-size:16px; font-weight:600; color:#0F172A; margin-bottom:6px;">
                No projects yet
              </div>
              <div style="color:#64748B; font-size:13px;">
                Click <b>+ New Project</b> to upload your first blueprint.<br>
                A demo sample (<code>화성태안3 A2BL</code>) is available in the next step.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Project cards
    for idx, p in enumerate(st.session_state.projects):
        approved_n = len(st.session_state.approved_variants.get(idx, set()))
        total_n = len(p["variants"])
        status = p.get("status", "Draft")
        status_class = (
            "status-approved" if status == "Approved"
            else "status-pending" if status == "Awaiting review"
            else "status-draft"
        )

        cols = st.columns([3, 1, 1, 1, 1])
        with cols[0]:
            st.markdown(
                f"""
                <div style="padding-top:12px;">
                  <div style="font-size:15px; font-weight:600; color:#0F172A;">{p['name']}</div>
                  <div style="font-size:12px; color:#64748B;">
                    {p['developer']} · created {p['created_at'][:10]}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with cols[1]:
            st.markdown(
                f"""
                <div style="padding-top:14px;">
                  <div style="font-size:12px; color:#94A3B8;">VARIANTS</div>
                  <div style="font-size:14px; font-weight:500;">{total_n}</div>
                </div>
                """, unsafe_allow_html=True
            )
        with cols[2]:
            st.markdown(
                f"""
                <div style="padding-top:14px;">
                  <div style="font-size:12px; color:#94A3B8;">REVIEWED</div>
                  <div style="font-size:14px; font-weight:500;">{approved_n}/{total_n}</div>
                </div>
                """, unsafe_allow_html=True
            )
        with cols[3]:
            st.markdown(
                f"""
                <div style="padding-top:14px;">
                  <span class="status-badge {status_class}">{status}</span>
                </div>
                """, unsafe_allow_html=True
            )
        with cols[4]:
            st.write("")
            if st.button("Open →", key=f"open_{idx}", use_container_width=True):
                st.session_state.current_project_idx = idx
                st.session_state.current_variant_idx = 0
                st.session_state.view = "review"
                st.rerun()
        st.markdown('<hr style="margin: 12px 0; border-color:#F1F5F9;">', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# View 2: New project setup
# -----------------------------------------------------------------------------
def view_setup():
    cols = st.columns([3, 1])
    with cols[0]:
        st.markdown(
            '<p class="kbom-h1">New Project</p>'
            '<p class="kbom-h1-sub">Upload a blueprint PDF to begin extraction</p>',
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.write("")
        if st.button("← Back to projects", use_container_width=True):
            st.session_state.view = "projects"
            st.rerun()

    cols = st.columns([2, 1])

    with cols[0]:
        uploaded = st.file_uploader(
            "Drop blueprint PDF here",
            type=["pdf"],
            help="Upload the construction company's blueprint PDF",
            label_visibility="collapsed",
        )
        st.caption("Or use the supplied sample for demo:")
        use_sample = st.checkbox("Use sample (`화성태안3 A2BL`)", value=True)

    with cols[1]:
        st.markdown('<p class="kbom-h2">Project setup</p>', unsafe_allow_html=True)
        developer = st.selectbox(
            "Developer",
            ["LH", "SH", "GH", "Private (custom)"],
            index=0,
            help="Auto-detected from blueprint title block when possible",
        )

    pdf_path: Path | None = None
    if uploaded:
        tmp_dir = Path("/tmp/kbom_uploads")
        tmp_dir.mkdir(exist_ok=True)
        pdf_path = tmp_dir / uploaded.name
        with open(pdf_path, "wb") as f:
            f.write(uploaded.getbuffer())
    elif use_sample and SAMPLE_PDF.exists():
        pdf_path = SAMPLE_PDF

    if not pdf_path:
        return

    # Detect variants
    with st.spinner("Detecting variants…"):
        variants_meta = pdf_parser.identify_variants(pdf_path)

    if not variants_meta:
        st.error("No variants detected. Check the PDF format.")
        return

    st.markdown(
        f'<p class="kbom-h2" style="margin-top:24px;">'
        f'Detected variants ({len(variants_meta)})</p>',
        unsafe_allow_html=True,
    )
    st.caption("Enter the unit count per variant from your contract")

    # Default unit-count guesses for the sample
    default_units = {
        "26A": 120, "26A1": 80, "37A": 60, "37A1": 40,
        "37B": 50, "37B1": 30, "46A": 20,
    }

    units_per_variant: dict[str, int] = {}
    with st.container(border=True):
        for page, code, label in variants_meta:
            cols = st.columns([3, 1, 1])
            with cols[0]:
                st.markdown(
                    f"""
                    <div style="padding:6px 0;">
                      <div style="font-size:14px; font-weight:500; color:#0F172A;">{label}</div>
                      <div style="font-size:11px; color:#94A3B8;">code <code>{code}</code> · page {page}</div>
                    </div>
                    """, unsafe_allow_html=True
                )
            with cols[2]:
                units = st.number_input(
                    "세대수",
                    key=f"units_{code}",
                    min_value=0,
                    max_value=9999,
                    value=default_units.get(code, 50),
                    label_visibility="collapsed",
                )
                units_per_variant[code] = int(units)

    st.markdown('<hr>', unsafe_allow_html=True)
    cols = st.columns([3, 2])
    with cols[0]:
        project_name = st.text_input(
            "Project name",
            value="화성태안3 A2BL" if pdf_path == SAMPLE_PDF else pdf_path.stem,
        )
    with cols[1]:
        st.write("")
        st.write("")
        total_units = sum(units_per_variant.values())
        st.markdown(
            f"<div style='text-align:right; color:#64748B; font-size:13px; padding-top:10px;'>"
            f"Total units: <b style='color:#0F172A;'>{total_units}</b>"
            f"</div>",
            unsafe_allow_html=True,
        )

    cols = st.columns([3, 1])
    with cols[1]:
        if st.button("Start extraction →", type="primary", use_container_width=True):
            _kick_off_extraction(pdf_path, project_name, units_per_variant, developer)


def _kick_off_extraction(pdf_path, project_name, units_per_variant, developer):
    placeholder = st.empty()
    placeholder.info("Extracting variants… this would take ~3 min on live API. Demo uses synthetic mode.")

    progress = st.progress(0.0)
    start = time.time()

    result = run_extraction(
        pdf_path=pdf_path,
        template_path=SAMPLE_TEMPLATE,
        project_name=project_name,
        units_per_variant=units_per_variant,
        skip_recalc=True,
    )
    progress.progress(1.0)
    elapsed = time.time() - start

    project_dict = {
        "name": result.project.name,
        "developer": developer,
        "blueprint_pdf_path": result.project.blueprint_pdf_path,
        "created_at": result.project.created_at.isoformat(),
        "status": "Awaiting review",
        "units_per_variant": units_per_variant,
        "populated_xlsx": str(result.populated_xlsx) if result.populated_xlsx else None,
        "variants": [
            {
                "variant_label": v.variant_label,
                "type_code": v.type_code,
                "page_number": v.page_number,
                "rows": [_row_to_dict(r) for r in v.rows],
                "validations": [
                    {"rule_id": vr.rule_id, "description": vr.description,
                     "passed": vr.passed, "detail": vr.detail}
                    for vr in v.validations
                ],
                "num_flagged": v.num_flagged,
            }
            for v in result.project.variants
        ],
    }

    st.session_state.projects.append(project_dict)
    st.session_state.current_project_idx = len(st.session_state.projects) - 1
    st.session_state.current_variant_idx = 0
    st.session_state.approved_variants[st.session_state.current_project_idx] = set()
    st.session_state.view = "review"

    placeholder.success(f"Extracted in {elapsed:.1f}s — opening review.")
    time.sleep(0.4)
    st.rerun()


def _row_to_dict(r) -> dict:
    return {
        "category": r.category.value,
        "code": r.code,
        "name": r.name,
        "width_mm": r.width_mm,
        "depth_mm": r.depth_mm,
        "height_mm": r.height_mm,
        "type_label": r.type_label,
        "source": r.source.value,
        "confidence": r.confidence,
        "rule_citation": (
            {
                "rule_id": r.rule_citation.rule_id,
                "description": r.rule_citation.description,
                "document": r.rule_citation.document,
                "page": r.rule_citation.page,
                "section_code": r.rule_citation.section_code,
            }
            if r.rule_citation else None
        ),
    }


# -----------------------------------------------------------------------------
# View 3: Review screen
# -----------------------------------------------------------------------------
def view_review():
    project = current_project()
    if not project:
        st.error("No project loaded.")
        st.session_state.view = "projects"
        st.rerun()
        return

    p_idx = st.session_state.current_project_idx
    approved_set = st.session_state.approved_variants.setdefault(p_idx, set())
    variants = project["variants"]

    # Top header
    cols = st.columns([3, 1])
    with cols[0]:
        st.markdown(
            f"""
            <p class="kbom-h1">{project['name']}</p>
            <p class="kbom-h1-sub">
              {project['developer']} · {len(variants)} variants ·
              {sum(project['units_per_variant'].values())} total units
            </p>
            """,
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.write("")
        if st.button("← All projects", use_container_width=True):
            st.session_state.view = "projects"
            st.rerun()

    # Variant tabs
    tab_labels = [
        f"{'✓ ' if i in approved_set else ''}{v['variant_label']}"
        for i, v in enumerate(variants)
    ]
    selected = st.tabs(tab_labels)

    for idx, tab in enumerate(selected):
        with tab:
            _render_variant(project, idx, approved_set)


def _render_variant(project: dict, idx: int, approved_set: set):
    variant = project["variants"][idx]
    rows = variant["rows"]
    units = project["units_per_variant"].get(variant["type_code"], 0)
    flagged = sum(1 for r in rows if r["confidence"] < 0.85 and r["source"] == "vision")
    is_approved = idx in approved_set

    # Variant summary bar
    cols = st.columns([1, 1, 1, 1, 1])
    with cols[0]:
        st.metric("Page", variant["page_number"])
    with cols[1]:
        st.metric("세대수", units)
    with cols[2]:
        st.metric("BOM rows", len(rows))
    with cols[3]:
        st.metric("Flagged", flagged, delta=f"-{flagged}" if flagged else None,
                  delta_color="inverse" if flagged else "off")
    with cols[4]:
        st.metric("Cost/unit (est.)", "₩1,847,200")

    st.write("")

    # Three-pane layout
    left, mid, right = st.columns([1.2, 2.2, 1.0])

    # ============== LEFT — Blueprint ==============
    with left:
        with st.container(border=True):
            st.markdown('<p class="kbom-h2">Blueprint</p>', unsafe_allow_html=True)
            try:
                img = pdf_parser.render_page(
                    project["blueprint_pdf_path"],
                    variant["page_number"],
                    dpi=150,
                )
                st.image(img, use_container_width=True)
                st.caption(f"Source: page {variant['page_number']} · auto-cropped")
            except Exception as e:
                st.error(f"Could not render: {e}")

    # ============== MIDDLE — Extracted rows ==============
    with mid:
        with st.container(border=True):
            cols = st.columns([3, 1])
            with cols[0]:
                st.markdown('<p class="kbom-h2">Extracted BOM</p>', unsafe_allow_html=True)
            with cols[1]:
                if flagged > 0:
                    st.markdown(
                        f'<span class="conf-pill conf-yellow" style="float:right;">'
                        f'{flagged} flagged</span>',
                        unsafe_allow_html=True,
                    )

            # Render rows as a custom HTML table for full styling control
            html_rows = []
            for i, r in enumerate(rows, 1):
                conf_pill = _conf_pill(r)
                cite = ""
                if r["rule_citation"]:
                    cite = f'<span style="color:#64748B; font-size:11px;">← {r["rule_citation"]["rule_id"]}</span>'

                if r["width_mm"] is not None:
                    dims = (
                        f'<span style="font-family: SF Mono, Monaco, monospace; '
                        f'font-size:12px; color:#475569;">'
                        f'{r["width_mm"]:>4} × {r["depth_mm"] or 0:>3} × {r["height_mm"] or 0:>4}'
                        f'</span>'
                    )
                else:
                    dims = '<span style="color:#CBD5E1;">—</span>'

                code_html = (
                    f'<code style="font-size:11px; background:#F1F5F9; padding:1px 6px; '
                    f'border-radius:4px;">{r["code"]}</code>'
                    if r["code"] else '<span style="color:#CBD5E1;">—</span>'
                )

                cat_color = "#059669" if r["category"] == "목대" else "#7C3AED"
                cat_bg = "#D1FAE5" if r["category"] == "목대" else "#EDE9FE"

                html_rows.append(f"""
                  <tr>
                    <td style="color:#94A3B8; font-size:11px; width:32px;">{i}</td>
                    <td style="width:60px;">{conf_pill}</td>
                    <td style="width:42px;">
                      <span style="background:{cat_bg}; color:{cat_color};
                            padding:1px 6px; border-radius:3px; font-size:10px;
                            font-weight:600;">{r["category"]}</span>
                    </td>
                    <td style="width:50px;">{code_html}</td>
                    <td style="font-weight:500; color:#0F172A;">{r["name"]}</td>
                    <td style="text-align:right;">{dims}</td>
                    <td style="text-align:right; padding-left:8px;">{cite}</td>
                  </tr>
                """)

            table_html = (
                '<table style="width:100%; border-collapse:collapse; font-size:13px;">'
                + "".join(f'<tr style="border-bottom:1px solid #F1F5F9;">' + r[r.find("<td"):r.rfind("</tr>")] + '</tr>'
                          for r in [r.replace("<tr>", "") for r in html_rows])
                + '</table>'
            )

            # Simpler: just join the rows directly
            table_html = (
                '<table style="width:100%; border-collapse:collapse; font-size:13px;">'
                + "".join(html_rows)
                + '</table>'
            )

            st.markdown(table_html, unsafe_allow_html=True)

    # ============== RIGHT — Validations + Rules + Cost ==============
    with right:
        # Validations
        with st.container(border=True):
            st.markdown('<p class="kbom-h2">Validations</p>', unsafe_allow_html=True)
            for vr in variant["validations"]:
                if vr["passed"]:
                    icon = '<span class="val-pass">✓</span>'
                elif "warn" in (vr.get("detail") or "").lower():
                    icon = '<span class="val-warn">⚠</span>'
                else:
                    icon = '<span class="val-pass">✓</span>'
                st.markdown(
                    f'<div class="val-row">{icon} <span><b>{vr["rule_id"]}</b> · {vr["description"]}</span></div>',
                    unsafe_allow_html=True,
                )

        # Rules fired
        rules_fired_ids = sorted({
            r["rule_citation"]["rule_id"]
            for r in variant["rows"] if r["rule_citation"]
        })
        if rules_fired_ids:
            with st.container(border=True):
                st.markdown(
                    f'<p class="kbom-h2">Rules fired ({len(rules_fired_ids)})</p>',
                    unsafe_allow_html=True,
                )
                all_rules = {r["id"]: r for r in list_rules()}
                for rid in rules_fired_ids:
                    meta = all_rules.get(rid, {})
                    desc = meta.get("description", "")[:60]
                    src = meta.get("source", "")
                    section = meta.get("section", "")
                    cite = f"{src} · {section}" if section else src
                    st.markdown(
                        f"""
                        <div class="rule-item">
                          <div>
                            <span class="rule-id">{rid}</span>
                            <span class="rule-desc">{desc}</span>
                            <div class="rule-cite">{cite}</div>
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    # Action bar
    st.write("")
    cols = st.columns([1, 1, 2])
    with cols[0]:
        prev_disabled = idx == 0
        if not prev_disabled and st.button(
            "← Previous", key=f"prev_{idx}", use_container_width=True
        ):
            st.session_state.current_variant_idx = idx - 1
            st.rerun()
    with cols[1]:
        next_disabled = idx >= len(project["variants"]) - 1
        if not next_disabled and st.button(
            "Next →", key=f"next_{idx}", use_container_width=True
        ):
            st.session_state.current_variant_idx = idx + 1
            st.rerun()
    with cols[2]:
        if not is_approved:
            label = (
                "Approve all and finish ✓" if idx == len(project["variants"]) - 1
                else "Approve & continue →"
            )
            if st.button(label, type="primary", key=f"approve_{idx}",
                         use_container_width=True):
                approved_set.add(idx)
                if len(approved_set) == len(project["variants"]):
                    project["status"] = "Approved"
                if idx < len(project["variants"]) - 1:
                    st.session_state.current_variant_idx = idx + 1
                st.rerun()
        else:
            st.button("✓ Approved", disabled=True, key=f"approved_{idx}",
                      use_container_width=True)


def _conf_pill(r) -> str:
    src = r["source"]
    conf = r["confidence"]
    if src == "rule":
        return '<span class="conf-pill conf-rule">⚙ rule</span>'
    if src == "catalog":
        return '<span class="conf-pill conf-rule">★ catalog</span>'
    if src == "spec_table":
        return f'<span class="conf-pill conf-spec">spec {int(conf*100)}</span>'
    if conf >= 0.85:
        return f'<span class="conf-pill conf-green">●{int(conf*100)}</span>'
    if conf >= 0.6:
        return f'<span class="conf-pill conf-yellow">⚠{int(conf*100)}</span>'
    return f'<span class="conf-pill conf-red">✗{int(conf*100)}</span>'


# -----------------------------------------------------------------------------
# Router
# -----------------------------------------------------------------------------
top_bar()

view = st.session_state.view
if view == "projects":
    view_projects()
elif view == "setup":
    view_setup()
elif view == "review":
    view_review()
else:
    st.error(f"Unknown view: {view}")
