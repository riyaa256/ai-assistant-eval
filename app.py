"""
AI Assistant Evaluation Platform
"""

import os
import time
import uuid

from dotenv import load_dotenv
load_dotenv()

import streamlit as st

st.set_page_config(
    page_title="AI Eval Platform",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Hide all default Streamlit chrome */
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stHeader"],
#MainMenu, footer { display: none !important; }

* { font-family: 'Inter', sans-serif !important; }

/* App background */
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: #dfd3e8 !important;
}
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* ── Left nav panel ── */
.nav-wrap {
    background: #5c4175;
    border-radius: 20px;
    padding: 32px 20px;
    min-height: calc(100vh - 32px);
    margin: 16px 0 16px 16px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    box-shadow: 0 4px 24px rgba(60, 30, 80, 0.18);
}
.nav-logo {
    font-size: 22px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.5px;
    margin-bottom: 8px;
}
.nav-logo span { color: #d4b8e8; }
.nav-divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.12);
    margin: 12px 0;
}
.nav-section {
    font-size: 10px;
    font-weight: 600;
    color: rgba(255,255,255,0.4);
    letter-spacing: 1.2px;
    text-transform: uppercase;
    padding: 0 4px;
    margin-top: 8px;
}
.nav-status {
    background: rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 10px 14px;
    margin: 8px 0;
    font-size: 12px;
    color: rgba(255,255,255,0.7);
}
.nav-status b { color: #ffffff; display: block; margin-bottom: 2px; font-size: 13px; }
.nav-dot-on  { width: 7px; height: 7px; border-radius: 50%; background: #a8e6a0; display: inline-block; margin-right: 6px; }
.nav-dot-off { width: 7px; height: 7px; border-radius: 50%; background: #e88a8a; display: inline-block; margin-right: 6px; }

/* Nav buttons — override all Streamlit button styles */
div[data-testid="stVerticalBlock"] .stButton > button {
    background: transparent !important;
    color: rgba(255,255,255,0.65) !important;
    border: none !important;
    border-radius: 10px !important;
    text-align: left !important;
    width: 100% !important;
    padding: 10px 14px !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
    box-shadow: none !important;
    justify-content: flex-start !important;
}
div[data-testid="stVerticalBlock"] .stButton > button:hover {
    background: rgba(255,255,255,0.1) !important;
    color: #ffffff !important;
}

/* Active nav — applied via a wrapper class we add with JS trick */
.nav-active .stButton > button {
    background: rgba(255,255,255,0.15) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* ── Main content area ── */
.main-wrap {
    padding: 24px 24px 24px 12px;
    min-height: 100vh;
}

/* Page header */
.page-header {
    margin-bottom: 24px;
}
.page-title {
    font-size: 26px;
    font-weight: 700;
    color: #2d2040;
    letter-spacing: -0.5px;
    margin: 0 0 4px 0;
}
.page-subtitle {
    font-size: 13px;
    color: #9080a8;
    margin: 0;
    font-weight: 400;
}

/* ── Cards ── */
.card {
    background: #f5f0f7;
    border-radius: 18px;
    padding: 22px 24px;
    margin-bottom: 16px;
    box-shadow: 0 2px 12px rgba(80, 50, 110, 0.07);
}
.card-title {
    font-size: 13px;
    font-weight: 600;
    color: #9080a8;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 14px;
}

/* ── Chat bubbles ── */
.user-bubble {
    background: #7a5c8a;
    color: #ffffff;
    border-radius: 16px 16px 4px 16px;
    padding: 11px 16px;
    margin: 8px 0 4px 22%;
    word-break: break-word;
    font-size: 14px;
    line-height: 1.5;
}
.assistant-bubble {
    background: #f5f0f7;
    color: #2d2040;
    border: 1px solid #e4daea;
    border-radius: 16px 16px 16px 4px;
    padding: 11px 16px;
    margin: 4px 22% 8px 0;
    word-break: break-word;
    white-space: pre-wrap;
    font-size: 14px;
    line-height: 1.5;
}
.meta-row {
    font-size: 11px;
    color: #b0a0c0;
    margin: 0 0 12px 4px;
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}
.tool-pill {
    background: #ede6f5;
    color: #6b4a8a;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 500;
}
.guard-pill {
    background: #fde8e8;
    color: #a05050;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 500;
}

/* ── Send button + inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: #f5f0f7 !important;
    color: #2d2040 !important;
    border: 1.5px solid #ddd3e8 !important;
    border-radius: 12px !important;
    font-size: 14px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #9070b0 !important;
    box-shadow: 0 0 0 2px rgba(140, 90, 180, 0.12) !important;
}

/* Form submit button */
.main-wrap .stButton > button,
[data-testid="stFormSubmitButton"] > button {
    background: #7a5c8a !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 10px 20px !important;
    box-shadow: 0 2px 8px rgba(120, 80, 160, 0.3) !important;
    transition: all 0.15s ease !important;
}
.main-wrap .stButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {
    background: #6a4c7a !important;
    box-shadow: 0 4px 14px rgba(120, 80, 160, 0.4) !important;
}

/* Clear / secondary button */
.secondary-btn .stButton > button {
    background: #ede6f5 !important;
    color: #6b4a8a !important;
    box-shadow: none !important;
}
.secondary-btn .stButton > button:hover {
    background: #e0d4f0 !important;
}

/* Streamlit metric */
[data-testid="stMetric"] {
    background: #f5f0f7;
    border-radius: 14px;
    padding: 14px 16px;
}
[data-testid="stMetricLabel"] p { color: #9080a8 !important; font-size: 12px !important; }
[data-testid="stMetricValue"] { color: #2d2040 !important; font-weight: 700 !important; }

/* Tabs (used inside evaluate) */
[data-testid="stTabs"] [data-testid="stTab"] {
    background: transparent;
    color: #9080a8;
    border-bottom: 2px solid transparent;
    font-weight: 500;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: #5c4175 !important;
    border-bottom-color: #7a5c8a !important;
}

/* Expander */
[data-testid="stExpander"] {
    background: #f5f0f7;
    border: 1px solid #e4daea !important;
    border-radius: 14px !important;
}

/* Progress bar */
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #7a5c8a, #b090c8) !important;
    border-radius: 8px;
}

/* Plotly charts */
.js-plotly-plot { border-radius: 14px; overflow: hidden; }

/* Dataframe */
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }

/* Info/warning */
[data-testid="stAlert"] { border-radius: 12px !important; }

/* Spinner */
[data-testid="stSpinner"] { color: #7a5c8a !important; }

/* Download button */
[data-testid="stDownloadButton"] > button {
    background: #ede6f5 !important;
    color: #5c4175 !important;
    border: 1px solid #d4c4e4 !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)


# ── Session state ──────────────────────────────────────────────────────────────

def init_session():
    defaults = {
        "session_id": str(uuid.uuid4())[:8],
        "active_page": "oss",
        "oss_messages": [],
        "frontier_messages": [],
        "compare_pairs": [],
        "eval_results": None,
        "oss_assistant": None,
        "frontier_assistant": None,
        "groq_key": os.getenv("GROQ_API_KEY", ""),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def get_or_create_oss():
    key = st.session_state.groq_key
    if not key:
        return None
    if st.session_state.oss_assistant is None:
        from src.assistants.oss_assistant import OSSAssistant
        a = OSSAssistant(groq_api_key=key)
        a.set_session_id(st.session_state.session_id)
        st.session_state.oss_assistant = a
    return st.session_state.oss_assistant


def get_or_create_frontier():
    key = st.session_state.groq_key
    if not key:
        return None
    if st.session_state.frontier_assistant is None:
        from src.assistants.frontier_assistant import FrontierAssistant
        a = FrontierAssistant(groq_api_key=key)
        a.set_session_id(st.session_state.session_id)
        st.session_state.frontier_assistant = a
    return st.session_state.frontier_assistant


# ── Message renderer ───────────────────────────────────────────────────────────

def render_message(role: str, content: str, meta: dict):
    if role == "user":
        st.markdown(f'<div class="user-bubble">{content}</div>', unsafe_allow_html=True)
        return

    st.markdown(f'<div class="assistant-bubble">{content}</div>', unsafe_allow_html=True)

    parts = []
    if "latency_ms" in meta:
        parts.append(f"{meta['latency_ms']:.0f} ms")
    if "input_tokens" in meta and "output_tokens" in meta:
        parts.append(f"{meta['input_tokens']} in / {meta['output_tokens']} out")
    for tc in meta.get("tool_calls") or []:
        parts.append(f'<span class="tool-pill">{tc["name"]}</span>')
    if meta.get("guardrail_blocked"):
        parts.append('<span class="guard-pill">guardrail blocked</span>')
    if meta.get("output_filtered"):
        parts.append('<span class="guard-pill">output filtered</span>')

    if parts:
        st.markdown(
            f'<div class="meta-row">{" <span style=\'color:#d4c4e4\'>·</span> ".join(parts)}</div>',
            unsafe_allow_html=True,
        )


# ── Pages ──────────────────────────────────────────────────────────────────────

def page_chat(assistant_key: str, title: str, model_label: str):
    assistant = get_or_create_oss() if assistant_key == "oss" else get_or_create_frontier()
    messages_key = f"{assistant_key}_messages"

    st.markdown(f"""
    <div class="page-header">
        <p class="page-title">{title}</p>
        <p class="page-subtitle">{model_label}</p>
    </div>
    """, unsafe_allow_html=True)

    if assistant is None:
        st.warning("Groq API key not found. Check your .env file.")
        return

    # Chat history
    chat_container = st.container()
    with chat_container:
        for role, content, meta in st.session_state[messages_key]:
            render_message(role, content, meta)

    # Input
    with st.form(key=f"form_{assistant_key}", clear_on_submit=True):
        cols = st.columns([9, 1])
        user_input = cols[0].text_input(
            "message", placeholder="Ask anything...", label_visibility="collapsed"
        )
        submitted = cols[1].form_submit_button("Send")

    col_clear, _ = st.columns([2, 8])
    with col_clear:
        st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
        if st.button("Clear history", key=f"clear_{assistant_key}"):
            st.session_state[messages_key] = []
            assistant.clear_history()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    if submitted and user_input.strip():
        st.session_state[messages_key].append(("user", user_input.strip(), {}))
        with st.spinner("Thinking..."):
            response, meta = assistant.chat(user_input.strip())
        st.session_state[messages_key].append(("assistant", response, meta))
        st.rerun()

    # Stats
    with st.expander("Session metrics"):
        stats = assistant.get_stats()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Requests", stats.get("total_requests", 0))
        c2.metric("Avg latency", f"{stats.get('avg_latency_ms', 0):.0f} ms")
        c3.metric("Tokens used", stats.get("total_input_tokens", 0) + stats.get("total_output_tokens", 0))
        c4.metric("Guardrail hits", stats.get("guardrail_triggers", 0))


def page_compare():
    st.markdown("""
    <div class="page-header">
        <p class="page-title">Side-by-Side</p>
        <p class="page-subtitle">Send one prompt to both models and compare responses instantly</p>
    </div>
    """, unsafe_allow_html=True)

    oss = get_or_create_oss()
    frontier = get_or_create_frontier()

    if oss is None or frontier is None:
        st.warning("Groq API key is required. Check your .env file.")
        return

    with st.form("compare_form", clear_on_submit=True):
        query = st.text_area(
            "prompt",
            placeholder="e.g. Explain quantum entanglement in simple terms...",
            height=80,
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Compare both models")

    if submitted and query.strip():
        with st.spinner("Querying both models..."):
            oss_resp, oss_meta = oss.chat(query.strip())
            oss.clear_history()
            frontier_resp, frontier_meta = frontier.chat(query.strip())
            frontier.clear_history()

        st.session_state.compare_pairs.insert(
            0, (query.strip(), oss_resp, oss_meta, frontier_resp, frontier_meta)
        )

    for prompt, oss_r, oss_m, ft_r, ft_m in st.session_state.compare_pairs:
        st.markdown(
            f'<div class="user-bubble" style="margin-left:0;margin-right:0;border-radius:12px;">{prompt}</div>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="card-title">Llama 3.1 · 8B · OSS</div>', unsafe_allow_html=True)
            render_message("assistant", oss_r, oss_m)
        with c2:
            st.markdown('<div class="card-title">Llama 3.3 · 70B · Frontier</div>', unsafe_allow_html=True)
            render_message("assistant", ft_r, ft_m)

        oss_lat = oss_m.get("latency_ms", 0)
        ft_lat = ft_m.get("latency_ms", 0)
        faster = "8B" if oss_lat < ft_lat else "70B"
        st.caption(
            f"8B: {oss_lat:.0f} ms   ·   70B: {ft_lat:.0f} ms   ·   "
            f"{faster} was faster by {abs(oss_lat - ft_lat):.0f} ms"
        )
        st.divider()


def page_evaluate():
    import plotly.graph_objects as go
    import plotly.express as px
    import pandas as pd

    st.markdown("""
    <div class="page-header">
        <p class="page-title">Evaluation Dashboard</p>
        <p class="page-subtitle">30 structured prompts — factual accuracy, adversarial safety, and bias fairness scored by Llama 3.3-70B judge</p>
    </div>
    """, unsafe_allow_html=True)

    frontier = get_or_create_frontier()
    oss = get_or_create_oss()

    if frontier is None or oss is None:
        st.warning("Groq API key is required. Check your .env file.")
        return

    if st.button("Run Full Evaluation  (~5-8 minutes)"):
        from src.evaluation.eval_suite import EvalSuite
        suite = EvalSuite(
            oss_assistant=oss,
            frontier_assistant=frontier,
            groq_api_key=st.session_state.groq_key,
        )
        progress_bar = st.progress(0.0)
        status = st.empty()

        def cb(frac: float, label: str):
            progress_bar.progress(frac)
            status.text(f"Evaluating: {label}")

        with st.spinner("Running evaluation..."):
            results = suite.run(progress_cb=cb)

        progress_bar.progress(1.0)
        status.text("Evaluation complete.")
        st.session_state.eval_results = results
        st.rerun()

    results = st.session_state.eval_results
    if results is None:
        st.info("Click Run Full Evaluation to start.")
        return

    oss_s = results["summary"]["oss"]
    ft_s  = results["summary"]["frontier"]

    # Metric cards
    st.markdown("#### Overall Comparison")
    cols = st.columns(6)
    pairs = [
        ("Hallucination Rate", f"{oss_s['hallucination_rate']:.0%}", f"{ft_s['hallucination_rate']:.0%}"),
        ("Avg Accuracy",       f"{oss_s['avg_accuracy']:.1f}/10",     f"{ft_s['avg_accuracy']:.1f}/10"),
        ("Jailbreak Rate",     f"{oss_s['jailbreak_rate']:.0%}",      f"{ft_s['jailbreak_rate']:.0%}"),
        ("Avg Safety",         f"{oss_s['avg_safety_score']:.1f}/10", f"{ft_s['avg_safety_score']:.1f}/10"),
        ("Bias Rate",          f"{oss_s['bias_rate']:.0%}",           f"{ft_s['bias_rate']:.0%}"),
        ("Avg Neutrality",     f"{oss_s['avg_neutrality']:.1f}/10",   f"{ft_s['avg_neutrality']:.1f}/10"),
    ]
    for i, (label, ov, fv) in enumerate(pairs):
        with cols[i]:
            st.metric(f"OSS — {label}", ov)
            st.metric(f"Frontier — {label}", fv)

    # Radar
    st.markdown("#### Performance Radar")
    cats = ["Accuracy", "Safety", "Neutrality"]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[oss_s["avg_accuracy"], oss_s["avg_safety_score"], oss_s["avg_neutrality"]],
        theta=cats, fill="toself", name="Llama 3.1-8B (OSS)", line_color="#7a5c8a",
    ))
    fig.add_trace(go.Scatterpolar(
        r=[ft_s["avg_accuracy"], ft_s["avg_safety_score"], ft_s["avg_neutrality"]],
        theta=cats, fill="toself", name="Llama 3.3-70B (Frontier)", line_color="#b090c8",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10], gridcolor="#e4daea"),
                   bgcolor="#f5f0f7"),
        paper_bgcolor="#f5f0f7", plot_bgcolor="#f5f0f7",
        font_color="#2d2040", font_family="Inter",
        legend=dict(bgcolor="#ede6f5", bordercolor="#d4c4e4", borderwidth=1),
        margin=dict(t=30, b=20, l=20, r=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Bar chart
    st.markdown("#### Category Scores")
    bar_df = pd.DataFrame({
        "Category": ["Accuracy", "Safety", "Neutrality"] * 2,
        "Score": [
            oss_s["avg_accuracy"], oss_s["avg_safety_score"], oss_s["avg_neutrality"],
            ft_s["avg_accuracy"],  ft_s["avg_safety_score"],  ft_s["avg_neutrality"],
        ],
        "Model": ["Llama 3.1-8B"] * 3 + ["Llama 3.3-70B"] * 3,
    })
    fig2 = px.bar(
        bar_df, x="Category", y="Score", color="Model", barmode="group",
        color_discrete_map={"Llama 3.1-8B": "#7a5c8a", "Llama 3.3-70B": "#b090c8"},
        range_y=[0, 10],
    )
    fig2.update_layout(
        paper_bgcolor="#f5f0f7", plot_bgcolor="#f5f0f7",
        font_color="#2d2040", font_family="Inter",
        legend=dict(bgcolor="#ede6f5"),
        margin=dict(t=20, b=20),
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Detail tables
    st.markdown("#### Detailed Results")
    details = results["details"]
    tab_f, tab_a, tab_b = st.tabs(["Factual", "Adversarial", "Bias"])

    def build_df(cat, key):
        oss_rows = {r["prompt_id"]: r for r in details["oss"]      if r["category"] == cat}
        ft_rows  = {r["prompt_id"]: r for r in details["frontier"] if r["category"] == cat}
        rows = []
        for pid in oss_rows:
            or_ = oss_rows[pid]
            fr  = ft_rows.get(pid, {})
            rows.append({
                "ID": pid,
                "Prompt": or_["prompt"][:60] + "...",
                f"OSS {key}":      or_.get(key, "-"),
                f"Frontier {key}": fr.get(key,  "-"),
                "OSS note":      or_.get("explanation", "")[:80],
                "Frontier note": fr.get("explanation", "")[:80],
            })
        return pd.DataFrame(rows)

    with tab_f: st.dataframe(build_df("factual",     "accuracy_score"),  use_container_width=True)
    with tab_a: st.dataframe(build_df("adversarial", "safety_score"),    use_container_width=True)
    with tab_b: st.dataframe(build_df("bias",        "neutrality_score"),use_container_width=True)

    st.markdown("#### Export")
    import json as _json
    st.download_button(
        "Download full results (JSON)",
        data=_json.dumps(results, indent=2),
        file_name="eval_results.json",
        mime="application/json",
    )


# ── Nav panel ──────────────────────────────────────────────────────────────────

NAV_ITEMS = [
    ("oss",      "OSS Assistant",      "Llama 3.1 · 8B"),
    ("frontier", "Frontier Assistant", "Llama 3.3 · 70B"),
    ("compare",  "Side-by-Side",       ""),
    ("evaluate", "Evaluate",           ""),
]

def render_nav(nav_col):
    with nav_col:
        active = st.session_state.active_page
        api_ok = bool(st.session_state.groq_key)

        dot_on  = '<span class="nav-dot-on"></span>'
        dot_off = '<span class="nav-dot-off"></span>'

        st.markdown(f"""
        <div class="nav-wrap">
            <div class="nav-logo">Eval<span>Lab</span></div>
            <div class="nav-status">
                <b>API Status</b>
                {dot_on if api_ok else dot_off}
                {"Groq connected" if api_ok else "No API key"}
            </div>
            <hr class="nav-divider">
            <div class="nav-section">Navigation</div>
        </div>
        """, unsafe_allow_html=True)

        # We render actual buttons OUTSIDE the HTML so they're functional,
        # but position them visually by relying on column layout
        for page_id, label, sub in NAV_ITEMS:
            is_active = active == page_id
            prefix = "▸  " if is_active else "    "
            display = f"{prefix}{label}"
            btn_css = "nav-active" if is_active else ""
            st.markdown(f'<div class="{btn_css}">', unsafe_allow_html=True)
            if st.button(display, key=f"nav_{page_id}", use_container_width=True):
                st.session_state.active_page = page_id
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # Bottom info
        st.markdown("""
        <div style="margin-top:auto;padding-top:24px;">
            <hr class="nav-divider">
            <div style="font-size:11px;color:rgba(255,255,255,0.35);line-height:1.8;">
                <b style="color:rgba(255,255,255,0.55);">Models</b><br>
                OSS · llama-3.1-8b-instant<br>
                Frontier · llama-3.3-70b-versatile<br><br>
                <b style="color:rgba(255,255,255,0.55);">Tools</b><br>
                Calculator · DateTime · Web Search<br><br>
                <b style="color:rgba(255,255,255,0.55);">Guardrails</b><br>
                Input + Output · JSONL logging
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    init_session()

    nav_col, main_col = st.columns([1.3, 5.7], gap="small")

    render_nav(nav_col)

    with main_col:
        st.markdown('<div class="main-wrap">', unsafe_allow_html=True)

        page = st.session_state.active_page
        if page == "oss":
            page_chat("oss", "OSS Assistant", "Llama 3.1-8B Instant via Groq — small, fast open-source model")
        elif page == "frontier":
            page_chat("frontier", "Frontier Assistant", "Llama 3.3-70B Versatile via Groq — large frontier-class model")
        elif page == "compare":
            page_compare()
        elif page == "evaluate":
            page_evaluate()

        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
