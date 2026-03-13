"""
streamlit_app.py  –  Student Performance Analytics & Prediction System
Dark Mode UI — all text perfectly visible.
Run:  streamlit run app/streamlit_app.py
"""

import os, sys, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import streamlit as st

warnings.filterwarnings("ignore")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from src.predict         import predict_single, load_meta, FEATURE_COLS
from src.recommendations import analyse
from src.db_manager      import (
    init_db, insert_prediction, search_records,
    get_student_trend, get_summary_stats, delete_record,
)
from src.train_model import train, DATA_PATH, MODEL_PATH

def make_html_table(df, level_col=None):
    """Render a DataFrame as a styled dark-mode HTML table."""
    level_colors = {
        "Excellent": ("background:#052e16", "color:#86efac"),
        "Good":      ("background:#0c1a3a", "color:#93c5fd"),
        "Average":   ("background:#1c1002", "color:#fcd34d"),
        "At Risk":   ("background:#1a0505", "color:#fca5a5"),
    }
    best_bg  = "background:#0f172a"
    head_css = "background:#0f172a;color:#94a3b8;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;padding:10px 14px;border-bottom:1px solid #334155;text-align:left"
    cell_css = "background:#1e293b;color:#e2e8f0;font-size:0.88rem;padding:9px 14px;border-bottom:1px solid #283548"
    best_css = "background:#1a2a1a;color:#86efac;font-size:0.88rem;padding:9px 14px;border-bottom:1px solid #283548;font-weight:700"

    html = f'''<div style="overflow-x:auto;border-radius:12px;border:1px solid #334155">
<table style="width:100%;border-collapse:collapse;font-family:Inter,sans-serif">
<thead><tr>'''
    for col in df.columns:
        html += f'<th style="{head_css}">{col}</th>'
    html += "</tr></thead><tbody>"

    for _, row in df.iterrows():
        html += "<tr>"
        for col in df.columns:
            val = row[col]
            if col == level_col and val in level_colors:
                bg, fg = level_colors[val]
                html += f'<td style="{bg};{fg};font-size:0.82rem;font-weight:700;padding:9px 14px;border-bottom:1px solid #283548;border-radius:4px">{val}</td>'
            elif col in ["RMSE ↓","MAE ↓","R² ↑"]:
                html += f'<td style="{cell_css}">{val}</td>'
            else:
                html += f'<td style="{cell_css}">{val}</td>'
        html += "</tr>"

    html += "</tbody></table></div>"
    return html


# ── Matplotlib dark style (applied globally to all charts) ───────────────────
CHART_BG    = "#1e293b"
CHART_TEXT  = "#e2e8f0"
CHART_GRID  = "#334155"
CHART_SPINE = "#475569"

def apply_dark_style(fig, ax_list):
    """Apply consistent dark styling to any matplotlib figure."""
    fig.patch.set_facecolor(CHART_BG)
    if not isinstance(ax_list, list):
        ax_list = [ax_list]
    for ax in ax_list:
        ax.set_facecolor(CHART_BG)
        ax.tick_params(colors=CHART_TEXT, labelsize=9)
        ax.xaxis.label.set_color(CHART_TEXT)
        ax.yaxis.label.set_color(CHART_TEXT)
        ax.title.set_color(CHART_TEXT)
        for spine in ax.spines.values():
            spine.set_edgecolor(CHART_SPINE)
        ax.grid(color=CHART_GRID, linewidth=0.6, alpha=0.6)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Student Performance Analytics",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS: Dark mode with EVERY text element explicitly coloured ────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Syne:wght@700;800&display=swap');

/* ═══ GLOBAL RESET ═══════════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

html, body {
    background-color: #0f172a !important;
    color: #f1f5f9 !important;
    font-family: 'Inter', sans-serif !important;
}

/* Every possible Streamlit wrapper */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="block-container"],
.main, .main > div,
div.block-container {
    background-color: #0f172a !important;
    color: #f1f5f9 !important;
}

/* ═══ UNIVERSAL TEXT — catches every element ═════════════════════════ */
p, h1, h2, h3, h4, h5, h6,
span, li, a, label, div,
.stMarkdown, .stMarkdown *,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] *,
[data-testid="stText"],
[data-testid="stText"] * {
    color: #f1f5f9 !important;
}

/* ═══ SIDEBAR ════════════════════════════════════════════════════════ */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div {
    background: #0a0f1e !important;
    border-right: 1px solid #1e293b !important;
}
[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] .stRadio label {
    color: #cbd5e1 !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] hr {
    border-color: #1e293b !important;
}

/* ═══ METRICS ════════════════════════════════════════════════════════ */
[data-testid="metric-container"] {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 14px !important;
    padding: 1rem 1.3rem !important;
}
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] * {
    color: #94a3b8 !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] * {
    color: #f8fafc !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"],
[data-testid="stMetricDelta"] * {
    color: #94a3b8 !important;
}

/* ═══ FORM ═══════════════════════════════════════════════════════════ */
[data-testid="stForm"] {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 16px !important;
    padding: 1.5rem 2rem !important;
}

/* ═══ INPUT LABELS ═══════════════════════════════════════════════════ */
.stTextInput > label,
.stTextInput > label *,
.stNumberInput > label,
.stNumberInput > label *,
.stSlider > label,
.stSlider > label *,
.stSelectbox > label,
.stSelectbox > label *,
.stRadio > label,
.stRadio > label *,
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] * {
    color: #cbd5e1 !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
}

/* ═══ INPUT FIELDS ═══════════════════════════════════════════════════ */
.stTextInput input,
.stNumberInput input,
input[type="text"],
input[type="number"] {
    background: #0f172a !important;
    border: 1.5px solid #475569 !important;
    border-radius: 8px !important;
    color: #f1f5f9 !important;
    caret-color: #3b82f6 !important;
}
.stTextInput input::placeholder,
.stNumberInput input::placeholder {
    color: #64748b !important;
}
.stTextInput input:focus,
.stNumberInput input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.2) !important;
    outline: none !important;
}

/* ═══ SLIDER ════════════════════════════════════════════════════════ */
[data-testid="stSlider"] [data-testid="stMarkdownContainer"] p {
    color: #94a3b8 !important;
    font-size: 0.8rem !important;
}
.stSlider [data-baseweb="slider"] [data-testid="stTickBar"] {
    color: #64748b !important;
}
/* Slider value labels */
.stSlider div[data-testid] {
    color: #e2e8f0 !important;
}

/* ═══ SELECTBOX ══════════════════════════════════════════════════════ */
[data-baseweb="select"] > div,
[data-baseweb="select"] > div *,
[data-baseweb="popover"] *,
[role="listbox"] *,
[role="option"] * {
    background: #1e293b !important;
    color: #f1f5f9 !important;
    border-color: #475569 !important;
}

/* ═══ BUTTON ════════════════════════════════════════════════════════ */
.stButton > button,
.stButton > button * {
    background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.6rem 2rem !important;
    box-shadow: 0 4px 15px rgba(59,130,246,0.4) !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(59,130,246,0.5) !important;
}

/* ═══ ALERTS ════════════════════════════════════════════════════════ */
/* Success */
[data-testid="stAlert"][kind="success"],
.stSuccess, .element-container .stSuccess {
    background: #052e16 !important;
    border: 1px solid #16a34a !important;
    border-radius: 10px !important;
}
[data-testid="stAlert"][kind="success"] *,
.stSuccess * {
    color: #86efac !important;
}
/* Info */
[data-testid="stAlert"][kind="info"],
.stInfo {
    background: #0c1a3a !important;
    border: 1px solid #1d4ed8 !important;
    border-radius: 10px !important;
}
[data-testid="stAlert"][kind="info"] *,
.stInfo * {
    color: #93c5fd !important;
}
/* Warning */
[data-testid="stAlert"][kind="warning"],
.stWarning {
    background: #1c1002 !important;
    border: 1px solid #d97706 !important;
    border-radius: 10px !important;
}
[data-testid="stAlert"][kind="warning"] *,
.stWarning * {
    color: #fcd34d !important;
}
/* Error */
[data-testid="stAlert"][kind="error"],
.stError {
    background: #1a0505 !important;
    border: 1px solid #dc2626 !important;
    border-radius: 10px !important;
}
[data-testid="stAlert"][kind="error"] *,
.stError * {
    color: #fca5a5 !important;
}

/* ═══ DATAFRAME ══════════════════════════════════════════════════════ */
[data-testid="stDataFrame"] { border-radius: 12px !important; overflow: hidden; }
/* Table header */
[data-testid="stDataFrame"] th,
[data-testid="stDataFrame"] .col_heading,
[data-testid="stDataFrame"] .row_heading,
[data-testid="stDataFrame"] thead tr th {
    background: #0f172a !important;
    color: #94a3b8 !important;
    font-weight: 700 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    border-bottom: 1px solid #334155 !important;
}
/* Table cells */
[data-testid="stDataFrame"] td,
[data-testid="stDataFrame"] .data,
[data-testid="stDataFrame"] tbody tr td {
    background: #1e293b !important;
    color: #e2e8f0 !important;
    border-bottom: 1px solid #334155 !important;
    font-size: 0.88rem !important;
}
[data-testid="stDataFrame"] tbody tr:hover td {
    background: #273548 !important;
}
/* Scrollbar */
[data-testid="stDataFrame"] ::-webkit-scrollbar { width: 6px; height: 6px; }
[data-testid="stDataFrame"] ::-webkit-scrollbar-track { background: #0f172a; }
[data-testid="stDataFrame"] ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
/* Glide data table specific */
.dvn-scroller { background: #1e293b !important; }
.gdg-cell { color: #e2e8f0 !important; background: #1e293b !important; }
.gdg-cell[data-testid] { color: #e2e8f0 !important; }

/* ═══ EXPANDER ═══════════════════════════════════════════════════════ */
details,
[data-testid="stExpander"],
[data-testid="stExpander"] > div {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 12px !important;
}
details summary,
details summary *,
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary * {
    color: #e2e8f0 !important;
    font-weight: 600 !important;
}

/* ═══ CAPTION / SMALL TEXT ═══════════════════════════════════════════ */
.stCaption, small, caption,
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] * {
    color: #64748b !important;
}

/* ═══ DIVIDERS ═══════════════════════════════════════════════════════ */
hr { border-color: #1e293b !important; }

/* ════════════════════════════════════════════════════════════════════
   CUSTOM COMPONENT CLASSES
   ════════════════════════════════════════════════════════════════════ */

/* Page banner */
.pg-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #1d4ed8 100%);
    border: 1px solid #1e40af;
    border-radius: 18px;
    padding: 1.8rem 2.2rem;
    margin-bottom: 1.8rem;
    box-shadow: 0 8px 32px rgba(29,78,216,0.3);
    position: relative;
    overflow: hidden;
}
.pg-header::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.pg-header h1 {
    font-family: 'Syne', sans-serif !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
    color: #ffffff !important;
    margin: 0 !important;
    line-height: 1.2 !important;
}
.pg-header p {
    color: #93c5fd !important;
    margin: 0.5rem 0 0 0 !important;
    font-size: 1rem !important;
    font-weight: 400 !important;
}

/* Section title */
.sec-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: #e2e8f0 !important;
    border-bottom: 1px solid #334155;
    padding-bottom: 0.5rem;
    margin: 1.8rem 0 1rem 0;
}

/* Card wrapper */
.card {
    background: #1e293b !important;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 1.3rem 1.5rem;
    margin-bottom: 1rem;
}

/* Score display */
.score-hero {
    background: linear-gradient(135deg, #1e3a8a, #2563eb);
    border-radius: 16px;
    padding: 1.8rem 1rem;
    text-align: center;
    border: 1px solid #3b82f6;
    box-shadow: 0 8px 24px rgba(37,99,235,0.35);
}
.score-hero .snum {
    font-family: 'Syne', sans-serif;
    font-size: 4rem;
    font-weight: 800;
    color: #ffffff !important;
    line-height: 1;
    display: block;
}
.score-hero .slbl {
    color: #93c5fd !important;
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.5rem;
    display: block;
}

/* Level badge */
.lvl-badge {
    border-radius: 16px;
    padding: 1.5rem 1rem;
    text-align: center;
    border: 2px solid;
}
.lvl-badge .lemoji { font-size: 2.8rem; display: block; }
.lvl-badge .lname  { font-size: 1.25rem; font-weight: 700; display: block; margin-top: 0.4rem; }
.lvl-badge .lsub   { font-size: 0.78rem; font-weight: 500; display: block; margin-top: 0.2rem; opacity: 0.8; }

/* Summary insight box */
.insight-box {
    background: #0c1a3a;
    border: 1px solid #1d4ed8;
    border-left: 4px solid #3b82f6;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    height: 100%;
}
.insight-box p {
    color: #93c5fd !important;
    margin: 0;
    font-size: 0.95rem;
    line-height: 1.7;
}

/* Strength / weakness tags */
.stag {
    display: inline-block;
    background: #052e16;
    color: #86efac !important;
    border: 1px solid #16a34a;
    border-radius: 999px;
    padding: 0.3rem 0.85rem;
    font-size: 0.82rem;
    font-weight: 600;
    margin: 0.25rem;
}
.wtag {
    display: inline-block;
    background: #1a0505;
    color: #fca5a5 !important;
    border: 1px solid #dc2626;
    border-radius: 999px;
    padding: 0.3rem 0.85rem;
    font-size: 0.82rem;
    font-weight: 600;
    margin: 0.25rem;
}

/* Recommendation item */
.rec-row {
    display: flex;
    align-items: flex-start;
    gap: 0.85rem;
    background: #1e293b !important;
    border: 1px solid #334155;
    border-left: 4px solid #3b82f6;
    border-radius: 12px;
    padding: 0.85rem 1.1rem;
    margin: 0.4rem 0;
}
.rec-row .rnum {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: #1d4ed8;
    color: #ffffff !important;
    border-radius: 50%;
    min-width: 28px;
    height: 28px;
    font-weight: 700;
    font-size: 0.8rem;
    flex-shrink: 0;
}
.rec-row .rtxt {
    color: #e2e8f0 !important;
    font-size: 0.93rem;
    line-height: 1.5;
    padding-top: 0.15rem;
}

/* Small info label */
.info-label {
    color: #64748b !important;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.3rem;
    display: block;
}

/* Sidebar model info */
.model-badge {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 0.7rem 1rem;
    margin: 0.4rem 0;
}
.model-badge span {
    color: #94a3b8 !important;
    font-size: 0.82rem;
}
.model-badge strong {
    color: #e2e8f0 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Bootstrap model ───────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="🤖 Training model on first run…")
def ensure_model():
    if not os.path.exists(MODEL_PATH):
        os.chdir(ROOT)
        train()
    return load_meta()

os.chdir(ROOT)
init_db()
model_meta = ensure_model()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<h2 style='color:#f8fafc;font-family:Syne,sans-serif;font-weight:800;"
        "margin-bottom:0.2rem'>🎓 Student<br>Analytics</h2>",
        unsafe_allow_html=True,
    )
    st.markdown("<hr>", unsafe_allow_html=True)

    page = st.radio(
        "NAVIGATION",
        ["🎯  Predict Performance", "📊  Analytics Dashboard", "📁  Student History"],
    )

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<span style='color:#94a3b8;font-size:0.78rem;font-weight:700;letter-spacing:0.08em'>MODEL INFO</span>", unsafe_allow_html=True)

    if model_meta:
        for lbl, key in [("Algorithm","model_name"),("R² Score","r2"),("RMSE","rmse")]:
            val = model_meta.get(key, "—")
            st.markdown(
                f"<div class='model-badge'><span>{lbl}</span><br>"
                f"<strong>{val}</strong></div>",
                unsafe_allow_html=True,
            )

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<span style='color:#475569;font-size:0.78rem'>v1.0 · Streamlit + scikit-learn</span>", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 1 — PREDICT
# ═════════════════════════════════════════════════════════════════════════════
if "Predict" in page:

    st.markdown("""
    <div class="pg-header">
        <h1>🎯 Performance Predictor</h1>
        <p>Enter student academic details to get an AI-powered exam score prediction with personalised insights.</p>
    </div>""", unsafe_allow_html=True)

    with st.form("pred_form"):
        st.markdown("<span style='color:#94a3b8;font-size:0.78rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase'>👤 STUDENT INFORMATION</span>", unsafe_allow_html=True)
        student_name = st.text_input("Student Name", placeholder="e.g. Rahul Sharma")

        st.markdown("<span style='color:#94a3b8;font-size:0.78rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;margin-top:1rem;display:block'>📋 ACADEMIC FEATURES</span>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            attendance            = st.slider("🏫 Attendance (%)", 0, 100, 80)
            study_hours           = st.slider("📚 Study Hours per Week", 0, 40, 15)
            participation_score   = st.slider("🙋 Class Participation (1–10)", 1, 10, 6)
            practice_test_score   = st.slider("📝 Practice Test Score (0–100)", 0, 100, 65)
        with col2:
            previous_gpa          = st.number_input("📈 Previous GPA (0.0–10.0)", 0.0, 10.0, 7.0, step=0.1)
            assignment_completion = st.slider("✅ Assignment Completion (%)", 0, 100, 75)
            sleep_hours           = st.slider("😴 Sleep Hours per Day", 3, 12, 7)
            practice_problems     = st.number_input("🧮 Practice Problems Completed", 0, 500, 60, step=5)

        submitted = st.form_submit_button("🔮  Predict Performance", width='stretch')

    if submitted:
        if not student_name.strip():
            st.warning("⚠️ Please enter a student name before predicting.")
        else:
            features = {
                "attendance": float(attendance), "previous_gpa": float(previous_gpa),
                "study_hours": float(study_hours), "assignment_completion": float(assignment_completion),
                "participation_score": float(participation_score), "sleep_hours": float(sleep_hours),
                "practice_test_score": float(practice_test_score), "practice_problems": int(practice_problems),
            }
            result   = predict_single(features)
            score    = result["predicted_score"]
            level    = result["performance_level"]
            emoji    = result["performance_emoji"]
            analysis = analyse(features, score)

            # Level colours (dark-mode safe)
            lvl_map = {
                "Excellent": ("#052e16", "#16a34a", "#86efac"),   # bg, border, text
                "Good":      ("#0c1a3a", "#1d4ed8", "#93c5fd"),
                "Average":   ("#1c1002", "#d97706", "#fcd34d"),
                "At Risk":   ("#1a0505", "#dc2626", "#fca5a5"),
            }
            lbg, lborder, ltxt = lvl_map.get(level, ("#1e293b","#475569","#e2e8f0"))

            insert_prediction(student_name.strip(), features, score, level)

            st.markdown("---")
            st.markdown("<div class='sec-title'>📊 Prediction Results</div>", unsafe_allow_html=True)

            r1, r2, r3 = st.columns([1,1,2])
            with r1:
                st.markdown(f"""
                <div class="score-hero">
                    <span class="snum">{score}</span>
                    <span class="slbl">Predicted Exam Score</span>
                </div>""", unsafe_allow_html=True)

            with r2:
                st.markdown(f"""
                <div class="lvl-badge" style="background:{lbg};border-color:{lborder};">
                    <span class="lemoji">{emoji}</span>
                    <span class="lname" style="color:{ltxt} !important;">{level}</span>
                    <span class="lsub" style="color:{ltxt} !important;">Performance Level</span>
                </div>""", unsafe_allow_html=True)

            with r3:
                st.markdown(f"""
                <div class="insight-box">
                    <p>💡 {analysis.summary}</p>
                </div>""", unsafe_allow_html=True)

            # ── Score gauge chart ─────────────────────────────────────────────
            st.markdown("<div class='sec-title'>📏 Score Gauge</div>", unsafe_allow_html=True)
            fig, ax = plt.subplots(figsize=(9, 2.4))
            apply_dark_style(fig, ax)

            zones = [
                (0,  50, "#7f1d1d", "#ef4444", "At Risk"),
                (50, 70, "#713f12", "#f59e0b", "Average"),
                (70, 85, "#1e3a8a", "#3b82f6", "Good"),
                (85,100, "#052e16", "#10b981", "Excellent"),
            ]
            for lo, hi, bg_c, bdr_c, lbl in zones:
                ax.barh(0, hi-lo, left=lo, height=0.55, color=bg_c, edgecolor=bdr_c, linewidth=1.2)
                ax.text((lo+hi)/2, -0.52, lbl, ha="center", va="top",
                        fontsize=8.5, color="#94a3b8", fontweight="600")

            ax.axvline(score, color="#f8fafc", linewidth=2.5, zorder=5)
            ax.plot(score, 0, "o", color="#f8fafc", markersize=12, zorder=6,
                    markeredgecolor="#1d4ed8", markeredgewidth=2)
            ax.text(score, 0.42, f"{score}", ha="center", va="bottom",
                    fontsize=12, fontweight="bold", color="#f8fafc")

            ax.set_xlim(0,100); ax.set_ylim(-0.82, 0.72)
            ax.set_yticks([])
            ax.set_xlabel("Score (0 – 100)", fontsize=9, color="#94a3b8")
            for s in ax.spines.values(): s.set_visible(False)
            ax.grid(False)
            plt.tight_layout()
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.pyplot(fig, width='stretch')
            st.markdown("</div>", unsafe_allow_html=True)
            plt.close(fig)

            # ── Strengths & Weaknesses ────────────────────────────────────────
            cs, cw = st.columns(2)
            with cs:
                st.markdown("<div class='sec-title'>✅ Strengths</div>", unsafe_allow_html=True)
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                if analysis.strengths:
                    st.markdown(" ".join(f'<span class="stag">✓ {s}</span>' for s in analysis.strengths), unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color:#64748b;font-style:italic'>No standout strengths yet.</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with cw:
                st.markdown("<div class='sec-title'>⚠️ Needs Improvement</div>", unsafe_allow_html=True)
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                if analysis.weaknesses:
                    st.markdown(" ".join(f'<span class="wtag">⚡ {w}</span>' for w in analysis.weaknesses), unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color:#86efac;font-weight:600'>All features above benchmarks! 🎉</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # ── Recommendations ───────────────────────────────────────────────
            st.markdown("<div class='sec-title'>🚀 Personalised Recommendations</div>", unsafe_allow_html=True)
            for i, rec in enumerate(analysis.recommendations, 1):
                st.markdown(f"""
                <div class="rec-row">
                    <span class="rnum">{i}</span>
                    <span class="rtxt">{rec}</span>
                </div>""", unsafe_allow_html=True)

            # ── Radar chart ───────────────────────────────────────────────────
            st.markdown("<div class='sec-title'>🕸️ Feature Radar Chart</div>", unsafe_allow_html=True)
            labels = ["Attendance","GPA","Study Hrs","Assignments","Participation","Sleep","Practice Test","Problems"]
            maxima = [100, 10.0, 40, 100, 10, 12, 100, 200]
            vals   = [attendance, previous_gpa, study_hours, assignment_completion,
                      participation_score, sleep_hours, practice_test_score, practice_problems]
            norm   = [v/m for v,m in zip(vals, maxima)] + [vals[0]/maxima[0]]
            angles = [n/len(labels)*2*np.pi for n in range(len(labels))] + [0]

            fig_r, ax_r = plt.subplots(figsize=(5,5), subplot_kw={"polar":True})
            fig_r.patch.set_facecolor(CHART_BG)
            ax_r.set_facecolor(CHART_BG)
            ax_r.plot(angles, norm, color="#3b82f6", linewidth=2.2)
            ax_r.fill(angles, norm, color="#3b82f6", alpha=0.18)

            ax_r.set_xticks(angles[:-1])
            ax_r.set_xticklabels(labels, size=9, color="#e2e8f0", fontweight="600")
            ax_r.set_ylim(0,1)
            ax_r.set_yticks([0.25,0.5,0.75,1.0])
            ax_r.set_yticklabels(["25%","50%","75%","100%"], size=7, color="#475569")
            ax_r.grid(color="#334155", linewidth=0.8)
            ax_r.spines["polar"].set_edgecolor("#334155")
            ax_r.set_title("Feature Profile", size=12, pad=20, color=CHART_TEXT, fontweight="bold")
            plt.tight_layout()

            _, rc, _ = st.columns([0.5,2,0.5])
            with rc:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.pyplot(fig_r, width='stretch')
                st.markdown("</div>", unsafe_allow_html=True)
            plt.close(fig_r)

            st.success(f"✅ Prediction saved for **{student_name.strip()}**!")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 2 — ANALYTICS DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
elif "Analytics" in page:

    st.markdown("""
    <div class="pg-header">
        <h1>📊 Analytics Dashboard</h1>
        <p>Explore dataset insights, model performance, and feature relationships.</p>
    </div>""", unsafe_allow_html=True)

    @st.cache_data
    def load_data():
        if not os.path.exists(DATA_PATH):
            from src.data_generator import save_dataset
            save_dataset(DATA_PATH)
        return pd.read_csv(DATA_PATH)

    df = load_data()

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("📋 Total Students", f"{len(df):,}")
    c2.metric("📊 Avg Exam Score",  f"{df['exam_score'].mean():.1f}")
    c3.metric("🏆 Highest Score",   f"{df['exam_score'].max():.1f}")
    c4.metric("🤖 Model R²",        f"{model_meta.get('r2','—')}")

    # Score distribution
    st.markdown("<div class='sec-title'>🎯 Exam Score Distribution</div>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    fig1, ax1 = plt.subplots(figsize=(10,3.8))
    apply_dark_style(fig1, ax1)
    n, bins, patches = ax1.hist(df["exam_score"], bins=30, edgecolor=CHART_BG, linewidth=0.8)
    for patch, left in zip(patches, bins[:-1]):
        if   left < 50: patch.set_facecolor("#ef4444")
        elif left < 70: patch.set_facecolor("#f59e0b")
        elif left < 85: patch.set_facecolor("#3b82f6")
        else:           patch.set_facecolor("#10b981")
    ax1.set_xlabel("Exam Score", fontsize=10, color=CHART_TEXT)
    ax1.set_ylabel("Number of Students", fontsize=10, color=CHART_TEXT)
    ax1.set_title("Score Distribution by Performance Zone", fontsize=13, fontweight="bold", color=CHART_TEXT)
    ax1.legend(handles=[
        mpatches.Patch(color="#ef4444",label="At Risk  (< 50)"),
        mpatches.Patch(color="#f59e0b",label="Average  (50–69)"),
        mpatches.Patch(color="#3b82f6",label="Good     (70–84)"),
        mpatches.Patch(color="#10b981",label="Excellent (85+)"),
    ], fontsize=9, loc="upper left",
       facecolor=CHART_BG, edgecolor=CHART_SPINE, labelcolor=CHART_TEXT)
    for s in ["top","right"]: ax1.spines[s].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig1, width='stretch')
    st.markdown("</div>", unsafe_allow_html=True)
    plt.close(fig1)

    # Feature importance
    st.markdown("<div class='sec-title'>🔬 Feature Importance</div>", unsafe_allow_html=True)
    fi = model_meta.get("feature_importances", {})
    if fi:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        fi_df = pd.DataFrame(fi.items(), columns=["Feature","Importance"])
        fi_df["Feature"] = fi_df["Feature"].map({
            "attendance":"Attendance","previous_gpa":"Previous GPA","study_hours":"Study Hours",
            "assignment_completion":"Assignment Completion","participation_score":"Participation Score",
            "sleep_hours":"Sleep Hours","practice_test_score":"Practice Test Score","practice_problems":"Practice Problems",
        })
        fi_df = fi_df.sort_values("Importance", ascending=True)
        fig2, ax2 = plt.subplots(figsize=(9,4))
        apply_dark_style(fig2, ax2)
        bar_cols = ["#3b82f6" if v==fi_df["Importance"].max() else "#1d4ed8" for v in fi_df["Importance"]]
        bars = ax2.barh(fi_df["Feature"], fi_df["Importance"], color=bar_cols, edgecolor="none", height=0.6)
        for bar, val in zip(bars, fi_df["Importance"]):
            ax2.text(bar.get_width()+0.002, bar.get_y()+bar.get_height()/2,
                     f"{val:.3f}", va="center", fontsize=9, color=CHART_TEXT, fontweight="500")
        ax2.set_xlabel("Importance Score", fontsize=10, color=CHART_TEXT)
        ax2.set_title("Feature Importance", fontsize=13, fontweight="bold", color=CHART_TEXT)
        ax2.tick_params(colors=CHART_TEXT)
        for s in ["top","right","left"]: ax2.spines[s].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig2, width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)
        plt.close(fig2)

    # Scatter plots
    st.markdown("<div class='sec-title'>🔍 Feature vs Exam Score</div>", unsafe_allow_html=True)

    def scatter(feat, xlabel, col):
        fig, ax = plt.subplots(figsize=(5,3.8))
        apply_dark_style(fig, ax)
        ax.scatter(df[feat], df["exam_score"], alpha=0.25, s=10, color=col)
        m, b = np.polyfit(df[feat], df["exam_score"], 1)
        xs = np.linspace(df[feat].min(), df[feat].max(), 100)
        ax.plot(xs, m*xs+b, color=col, linewidth=2.2)
        ax.set_xlabel(xlabel, fontsize=9, color=CHART_TEXT)
        ax.set_ylabel("Exam Score", fontsize=9, color=CHART_TEXT)
        ax.set_title(f"{xlabel} vs Score", fontsize=11, fontweight="bold", color=CHART_TEXT)
        for s in ["top","right"]: ax.spines[s].set_visible(False)
        plt.tight_layout()
        return fig

    ca, cb = st.columns(2)
    with ca:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        f = scatter("study_hours","Study Hours / Week","#3b82f6")
        st.pyplot(f, width='stretch'); plt.close(f)
        st.markdown("</div>", unsafe_allow_html=True)
    with cb:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        f = scatter("attendance","Attendance (%)","#10b981")
        st.pyplot(f, width='stretch'); plt.close(f)
        st.markdown("</div>", unsafe_allow_html=True)

    cc, cd = st.columns(2)
    with cc:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        f = scatter("practice_test_score","Practice Test Score","#f59e0b")
        st.pyplot(f, width='stretch'); plt.close(f)
        st.markdown("</div>", unsafe_allow_html=True)
    with cd:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        f = scatter("previous_gpa","Previous GPA","#a78bfa")
        st.pyplot(f, width='stretch'); plt.close(f)
        st.markdown("</div>", unsafe_allow_html=True)

    # Correlation heatmap
    st.markdown("<div class='sec-title'>🔥 Correlation Heatmap</div>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    nice = {"attendance":"Attendance","previous_gpa":"Prev GPA","study_hours":"Study Hrs",
            "assignment_completion":"Assignments","participation_score":"Participation",
            "sleep_hours":"Sleep","practice_test_score":"Practice Test",
            "practice_problems":"Problems","exam_score":"Exam Score"}
    corr = df.corr(numeric_only=True).rename(index=nice, columns=nice)
    fig3, ax3 = plt.subplots(figsize=(9,6))
    fig3.patch.set_facecolor(CHART_BG)
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0,
                linewidths=0.5, linecolor="#0f172a",
                annot_kws={"size":8,"color":"#f1f5f9","fontweight":"bold"}, ax=ax3)
    ax3.set_title("Feature Correlation Matrix", fontsize=13, fontweight="bold", color=CHART_TEXT, pad=12)
    ax3.tick_params(axis="x", rotation=30, labelsize=9, colors=CHART_TEXT)
    ax3.tick_params(axis="y", rotation=0,  labelsize=9, colors=CHART_TEXT)
    plt.tight_layout()
    st.pyplot(fig3, width='stretch')
    st.markdown("</div>", unsafe_allow_html=True)
    plt.close(fig3)

    # Model comparison
    st.markdown("<div class='sec-title'>🏆 Model Comparison</div>", unsafe_allow_html=True)
    all_r = model_meta.get("all_results",[])
    if all_r:
        cdf = pd.DataFrame(all_r)
        cdf.columns = ["Model","RMSE ↓","MAE ↓","R² ↑"]
        # Format numeric columns
        for col in ["RMSE ↓","MAE ↓","R² ↑"]:
            cdf[col] = cdf[col].apply(lambda x: f"{x:.4f}")
        # Highlight best model row
        best_idx = cdf["RMSE ↓"].astype(float).idxmin()
        cdf_html = make_html_table(cdf)
        st.markdown(cdf_html, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 3 — STUDENT HISTORY
# ═════════════════════════════════════════════════════════════════════════════
elif "History" in page:

    st.markdown("""
    <div class="pg-header">
        <h1>📁 Student History</h1>
        <p>Browse, search, and analyse all past predictions stored in the database.</p>
    </div>""", unsafe_allow_html=True)

    stats = get_summary_stats()
    if stats.get("total",0) > 0:
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("📋 Total Records", stats.get("total",0))
        c2.metric("📊 Avg Score",     f"{stats.get('avg_score',0):.1f}")
        c3.metric("🏆 Excellent",      stats.get("excellent",0))
        c4.metric("✅ Good",            stats.get("good",0))
        c5.metric("🚨 At Risk",        stats.get("at_risk",0))

    st.markdown("<div class='sec-title'>🔍 Search & Filter</div>", unsafe_allow_html=True)
    s1, s2 = st.columns([2,1])
    with s1: name_q = st.text_input("Search by student name", placeholder="Type a name…")
    with s2: lvl_f  = st.selectbox("Filter by level", ["All","Excellent","Good","Average","At Risk"])

    records = search_records(name_query=name_q, level_filter=None if lvl_f=="All" else lvl_f)

    if not records:
        st.info("📭 No records yet. Make some predictions first!")
    else:
        st.success(f"**{len(records)} record(s) found**")

        disp = ["id","student_name","predicted_score","performance_level",
                "attendance","study_hours","practice_test_score","timestamp"]
        rdf  = pd.DataFrame(records)[disp]
        rdf.columns = ["ID","Student","Score","Level","Attendance","Study Hrs","Practice Test","Timestamp"]

        def clr(val):
            m = {
                "Excellent": "background-color:#052e16;color:#86efac",
                "Good":      "background-color:#0c1a3a;color:#93c5fd",
                "Average":   "background-color:#1c1002;color:#fcd34d",
                "At Risk":   "background-color:#1a0505;color:#fca5a5",
            }
            return m.get(val,"")

        # Format columns
        rdf["Score"]      = rdf["Score"].apply(lambda x: f"{float(x):.1f}")
        rdf["Attendance"] = rdf["Attendance"].apply(lambda x: f"{float(x):.0f}%")
        st.markdown(make_html_table(rdf, level_col="Level"), unsafe_allow_html=True)

        # Pie
        st.markdown("<div class='sec-title'>📊 Performance Distribution</div>", unsafe_allow_html=True)
        lc = pd.DataFrame(records)["performance_level"].value_counts()
        pc = {"Excellent":"#10b981","Good":"#3b82f6","Average":"#f59e0b","At Risk":"#ef4444"}

        fig_p, ax_p = plt.subplots(figsize=(5,4))
        fig_p.patch.set_facecolor(CHART_BG)
        ax_p.set_facecolor(CHART_BG)
        wedges, texts, autotexts = ax_p.pie(
            lc.values, labels=lc.index,
            colors=[pc.get(l,"#94a3b8") for l in lc.index],
            autopct="%1.1f%%", startangle=140,
            wedgeprops={"edgecolor":CHART_BG,"linewidth":2.5},
        )
        for t in texts:     t.set_color(CHART_TEXT); t.set_fontsize(10)
        for t in autotexts: t.set_color("#ffffff");   t.set_fontsize(9); t.set_fontweight("bold")
        ax_p.set_title("Performance Breakdown", fontsize=12, fontweight="bold", color=CHART_TEXT, pad=12)
        plt.tight_layout()

        _, pc2, _ = st.columns([1,2,1])
        with pc2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.pyplot(fig_p, width='stretch')
            st.markdown("</div>", unsafe_allow_html=True)
        plt.close(fig_p)

        # Trend
        st.markdown("<div class='sec-title'>📈 Individual Student Trend</div>", unsafe_allow_html=True)
        names = sorted(set(r["student_name"] for r in records))
        sel   = st.selectbox("Select student", names)
        if sel:
            trend = get_student_trend(sel)
            if len(trend) < 2:
                st.info("Need at least 2 predictions for this student to show a trend.")
            else:
                tdf = pd.DataFrame(trend)
                fig_t, ax_t = plt.subplots(figsize=(9,3.8))
                apply_dark_style(fig_t, ax_t)
                ax_t.plot(range(len(tdf)), tdf["predicted_score"], marker="o",
                          color="#3b82f6", linewidth=2.5, markersize=9, zorder=5,
                          markerfacecolor="#f8fafc", markeredgecolor="#3b82f6", markeredgewidth=2)
                ax_t.fill_between(range(len(tdf)), tdf["predicted_score"], alpha=0.12, color="#3b82f6")
                for score_val, color_val, label_val in [
                    (85, "#10b981", "Excellent (85)"),
                    (70, "#f59e0b", "Good (70)"),
                    (50, "#ef4444", "At Risk (50)"),
                ]:
                    ax_t.axhline(score_val, color=color_val, linestyle="--", linewidth=1.2,
                                 label=label_val, alpha=0.7)
                ax_t.set_xticks(range(len(tdf)))
                ax_t.set_xticklabels([t["timestamp"][:10] for t in trend],
                                      rotation=20, fontsize=8, color=CHART_TEXT)
                ax_t.set_ylabel("Predicted Score", fontsize=10, color=CHART_TEXT)
                ax_t.set_title(f"Performance Trend — {sel}", fontsize=12,
                               fontweight="bold", color=CHART_TEXT)
                ax_t.legend(fontsize=8, loc="lower right",
                            facecolor=CHART_BG, edgecolor=CHART_SPINE, labelcolor=CHART_TEXT)
                ax_t.set_ylim(0,105)
                for s in ["top","right"]: ax_t.spines[s].set_visible(False)
                plt.tight_layout()
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.pyplot(fig_t, width='stretch')
                st.markdown("</div>", unsafe_allow_html=True)
                plt.close(fig_t)

        with st.expander("🗑️  Delete a Record"):
            del_id = st.number_input("Record ID to delete", min_value=1, step=1)
            if st.button("Delete Record"):
                delete_record(int(del_id))
                st.success(f"Record #{del_id} deleted. Refresh to see changes.")
