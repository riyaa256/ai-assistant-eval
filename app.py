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

/* Hide Streamlit chrome */
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stHeader"],
#MainMenu, footer { display: none !important; }

* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

/* ── App background ── */
[data-testid="stAppViewContainer"],
[data-testid="stMain"] { background: #c9b8dc !important; }

.block-container {
    padding: 16px !important;
    max-width: 100% !important;
}

/* ── NAV COLUMN — style the actual Streamlit column container ── */
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child {
    background: #4a3362 !important;
    border-radius: 20px !important;
    padding: 28px 16px !important;
    min-height: calc(100vh - 40px) !important;
    position: sticky !important;
    top: 20px !important;
    overflow: visible !important;
}

/* Remove extra gap/padding inside nav column */
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child > div[data-testid="stVerticalBlock"] {
    gap: 0 !important;
}

/* ── NAV BUTTONS ── */
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child .stButton > button {
    background: transparent !important;
    color: rgba(255,255,255,0.6) !important;
    border: none !important;
    border-radius: 10px !important;
    text-align: left !important;
    width: 100% !important;
    padding: 9px 14px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
    letter-spacing: 0.1px !important;
    justify-content: flex-start !important;
    margin-bottom: 2px !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child .stButton > button:hover {
    background: rgba(255,255,255,0.1) !important;
    color: #ffffff !important;
}

/* ── MAIN AREA ── */
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) {
    padding: 8px 12px 8px 4px !important;
}

/* ── ALL MAIN BUTTONS ── */
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) .stButton > button,
[data-testid="stFormSubmitButton"] > button {
    background: #6b4d88 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 11px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 10px 20px !important;
    box-shadow: 0 2px 8px rgba(80, 40, 120, 0.25) !important;
    transition: all 0.15s ease !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) .stButton > button:hover {
    background: #5a3d77 !important;
    box-shadow: 0 4px 14px rgba(80, 40, 120, 0.35) !important;
}

/* Secondary button override */
.secondary-btn button {
    background: #ede5f5 !important;
    color: #5a3d77 !important;
    box-shadow: none !important;
    font-weight: 500 !important;
}
.secondary-btn button:hover {
    background: #e0d3ef !important;
}

/* ── PAGE HEADER ── */
.page-title {
    font-size: 28px;
    font-weight: 700;
    color: #1a0f2e;
    letter-spacing: -0.6px;
    margin: 0 0 5px 0;
    line-height: 1.2;
}
.page-subtitle {
    font-size: 13px;
    color: #7a6090;
    margin: 0 0 24px 0;
    font-weight: 400;
}

/* ── CHAT BUBBLES ── */
.user-bubble {
    background: #6b4d88;
    color: #ffffff;
    border-radius: 16px 16px 4px 16px;
    padding: 11px 16px;
    margin: 8px 0 4px 20%;
    word-break: break-word;
    font-size: 14px;
    line-height: 1.55;
    box-shadow: 0 2px 8px rgba(80, 40, 120, 0.2);
}
.assistant-bubble {
    background: #f2ebfa;
    color: #1a0f2e;
    border: 1px solid #ddd0ee;
    border-radius: 16px 16px 16px 4px;
    padding: 11px 16px;
    margin: 4px 20% 4px 0;
    word-break: break-word;
    white-space: pre-wrap;
    font-size: 14px;
    line-height: 1.55;
}
.meta-row {
    font-size: 11px;
    color: #9a80b8;
    margin: 2px 0 12px 4px;
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
}
.tool-pill {
    background: #ece3f8;
    color: #5a3d77;
    border-radius: 20px;
    padding: 2px 9px;
    font-size: 11px;
    font-weight: 500;
    border: 1px solid #d8c8ef;
}
.guard-pill {
    background: #fde8e8;
    color: #a03030;
    border-radius: 20px;
    padding: 2px 9px;
    font-size: 11px;
    font-weight: 500;
}

/* ── CARD label ── */
.card-label {
    font-size: 11px;
    font-weight: 600;
    color: #8870a8;
    text-transform: uppercase;
    letter-spacing: 0.9px;
    margin-bottom: 10px;
}

/* ── INPUT FIELDS ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: #f2ebfa !important;
    color: #1a0f2e !important;
    border: 1.5px solid #cebde8 !important;
    border-radius: 12px !important;
    font-size: 14px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #8860b8 !important;
    box-shadow: 0 0 0 3px rgba(130, 80, 180, 0.12) !important;
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder { color: #b0a0c8 !important; }

/* ── METRICS ── */
[data-testid="stMetric"] {
    background: #f2ebfa;
    border-radius: 14px;
    padding: 14px 16px;
    border: 1px solid #ddd0ee;
}
[data-testid="stMetricLabel"] p { color: #7a6090 !important; font-size: 12px !important; }
[data-testid="stMetricValue"]   { color: #1a0f2e !important; font-weight: 700 !important; }

/* ── EXPANDER ── */
[data-testid="stExpander"] {
    background: #f2ebfa !important;
    border: 1px solid #ddd0ee !important;
    border-radius: 14px !important;
}
[data-testid="stExpander"] summary { color: #5a3d77 !important; font-weight: 600 !important; }

/* ── TABS ── */
[data-baseweb="tab-list"] { background: transparent !important; }
[data-baseweb="tab"] {
    color: #7a6090 !important;
    font-weight: 500 !important;
    font-size: 13px !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    color: #4a3362 !important;
    font-weight: 700 !important;
    border-bottom-color: #6b4d88 !important;
}

/* ── PROGRESS BAR ── */
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #6b4d88, #a880c8) !important;
    border-radius: 6px;
}

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] { border-radius: 12px !important; overflow: hidden; }

/* ── ALERTS ── */
[data-testid="stAlert"] { border-radius: 12px !important; }

/* ── DOWNLOAD BUTTON ── */
[data-testid="stDownloadButton"] > button {
    background: #ece3f8 !important;
    color: #4a3362 !important;
    border: 1px solid #cebde8 !important;
    border-radius: 11px !important;
    font-weight: 600 !important;
    box-shadow: none !important;
}

/* ── DIVIDER ── */
hr { border-color: rgba(255,255,255,0.12) !important; }
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
        sep = ' <span style="color:#cdbde8">·</span> '
        st.markdown(f'<div class="meta-row">{sep.join(parts)}</div>', unsafe_allow_html=True)


# ── Pages ──────────────────────────────────────────────────────────────────────

def page_chat(assistant_key: str, title: str, subtitle: str):
    assistant = get_or_create_oss() if assistant_key == "oss" else get_or_create_frontier()
    messages_key = f"{assistant_key}_messages"

    st.markdown(f'<p class="page-title">{title}</p><p class="page-subtitle">{subtitle}</p>', unsafe_allow_html=True)

    if assistant is None:
        st.warning("Groq API key not found. Check your .env file.")
        return

    for role, content, meta in st.session_state[messages_key]:
        render_message(role, content, meta)

    with st.form(key=f"form_{assistant_key}", clear_on_submit=True):
        cols = st.columns([10, 1.5])
        user_input = cols[0].text_input("msg", placeholder="Ask anything...", label_visibility="collapsed")
        submitted = cols[1].form_submit_button("Send")

    c1, _ = st.columns([2, 8])
    with c1:
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

    with st.expander("Session metrics"):
        stats = assistant.get_stats()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Requests",      stats.get("total_requests", 0))
        c2.metric("Avg latency",   f"{stats.get('avg_latency_ms', 0):.0f} ms")
        c3.metric("Tokens used",   stats.get("total_input_tokens", 0) + stats.get("total_output_tokens", 0))
        c4.metric("Guardrail hits",stats.get("guardrail_triggers", 0))


def page_compare():
    st.markdown('<p class="page-title">Side-by-Side</p><p class="page-subtitle">Send one prompt to both models and compare responses instantly</p>', unsafe_allow_html=True)

    oss = get_or_create_oss()
    frontier = get_or_create_frontier()
    if oss is None or frontier is None:
        st.warning("Groq API key is required. Check your .env file.")
        return

    with st.form("compare_form", clear_on_submit=True):
        query = st.text_area("prompt", placeholder="e.g. Explain quantum entanglement in simple terms...", height=80, label_visibility="collapsed")
        submitted = st.form_submit_button("Compare both models")

    if submitted and query.strip():
        with st.spinner("Querying both models..."):
            oss_resp, oss_meta = oss.chat(query.strip()); oss.clear_history()
            frontier_resp, frontier_meta = frontier.chat(query.strip()); frontier.clear_history()
        st.session_state.compare_pairs.insert(0, (query.strip(), oss_resp, oss_meta, frontier_resp, frontier_meta))

    for prompt, oss_r, oss_m, ft_r, ft_m in st.session_state.compare_pairs:
        st.markdown(f'<div class="user-bubble" style="margin-left:0;margin-right:0;border-radius:12px;">{prompt}</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="card-label">Llama 3.1 · 8B · OSS</div>', unsafe_allow_html=True)
            render_message("assistant", oss_r, oss_m)
        with c2:
            st.markdown('<div class="card-label">Llama 3.3 · 70B · Frontier</div>', unsafe_allow_html=True)
            render_message("assistant", ft_r, ft_m)
        oss_lat = oss_m.get("latency_ms", 0)
        ft_lat  = ft_m.get("latency_ms", 0)
        faster  = "8B" if oss_lat < ft_lat else "70B"
        st.caption(f"8B: {oss_lat:.0f} ms   ·   70B: {ft_lat:.0f} ms   ·   {faster} was faster by {abs(oss_lat - ft_lat):.0f} ms")
        st.divider()


def page_evaluate():
    import plotly.graph_objects as go
    import plotly.express as px
    import pandas as pd

    st.markdown('<p class="page-title">Evaluation Dashboard</p><p class="page-subtitle">30 structured prompts — factual accuracy, adversarial safety, and bias fairness · judge: Llama 3.3-70B</p>', unsafe_allow_html=True)

    oss = get_or_create_oss()
    frontier = get_or_create_frontier()
    if oss is None or frontier is None:
        st.warning("Groq API key is required. Check your .env file.")
        return

    if st.button("Run Full Evaluation  (approx. 5-8 minutes)"):
        from src.evaluation.eval_suite import EvalSuite
        suite = EvalSuite(oss_assistant=oss, frontier_assistant=frontier, groq_api_key=st.session_state.groq_key)
        pb = st.progress(0.0)
        status = st.empty()
        def cb(f, l):
            pb.progress(f); status.text(f"Evaluating: {l}")
        with st.spinner("Running evaluation..."):
            results = suite.run(progress_cb=cb)
        pb.progress(1.0); status.text("Evaluation complete.")
        st.session_state.eval_results = results
        st.rerun()

    results = st.session_state.eval_results
    if results is None:
        st.info("Click Run Full Evaluation to start.")
        return

    oss_s = results["summary"]["oss"]
    ft_s  = results["summary"]["frontier"]

    st.markdown("#### Overall Comparison")
    cols = st.columns(6)
    pairs = [
        ("Hallucination Rate", f"{oss_s['hallucination_rate']:.0%}", f"{ft_s['hallucination_rate']:.0%}"),
        ("Avg Accuracy",       f"{oss_s['avg_accuracy']:.1f}/10",   f"{ft_s['avg_accuracy']:.1f}/10"),
        ("Jailbreak Rate",     f"{oss_s['jailbreak_rate']:.0%}",    f"{ft_s['jailbreak_rate']:.0%}"),
        ("Avg Safety",         f"{oss_s['avg_safety_score']:.1f}/10",f"{ft_s['avg_safety_score']:.1f}/10"),
        ("Bias Rate",          f"{oss_s['bias_rate']:.0%}",         f"{ft_s['bias_rate']:.0%}"),
        ("Avg Neutrality",     f"{oss_s['avg_neutrality']:.1f}/10", f"{ft_s['avg_neutrality']:.1f}/10"),
    ]
    for i, (label, ov, fv) in enumerate(pairs):
        with cols[i]:
            st.metric(f"OSS — {label}", ov)
            st.metric(f"Frontier — {label}", fv)

    bg = "#f2ebfa"
    st.markdown("#### Performance Radar")
    cats = ["Accuracy", "Safety", "Neutrality"]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=[oss_s["avg_accuracy"], oss_s["avg_safety_score"], oss_s["avg_neutrality"]], theta=cats, fill="toself", name="Llama 3.1-8B (OSS)",      line_color="#6b4d88"))
    fig.add_trace(go.Scatterpolar(r=[ft_s["avg_accuracy"],  ft_s["avg_safety_score"],  ft_s["avg_neutrality"]],  theta=cats, fill="toself", name="Llama 3.3-70B (Frontier)", line_color="#b080d0"))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,10], gridcolor="#ddd0ee"), bgcolor=bg), paper_bgcolor=bg, plot_bgcolor=bg, font=dict(color="#1a0f2e", family="Inter"), legend=dict(bgcolor="#ece3f8", bordercolor="#cebde8", borderwidth=1), margin=dict(t=30,b=20,l=20,r=20))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Category Scores")
    bar_df = pd.DataFrame({
        "Category": ["Accuracy","Safety","Neutrality"]*2,
        "Score": [oss_s["avg_accuracy"],oss_s["avg_safety_score"],oss_s["avg_neutrality"], ft_s["avg_accuracy"],ft_s["avg_safety_score"],ft_s["avg_neutrality"]],
        "Model":  ["Llama 3.1-8B"]*3 + ["Llama 3.3-70B"]*3,
    })
    fig2 = px.bar(bar_df, x="Category", y="Score", color="Model", barmode="group", color_discrete_map={"Llama 3.1-8B":"#6b4d88","Llama 3.3-70B":"#b080d0"}, range_y=[0,10])
    fig2.update_layout(paper_bgcolor=bg, plot_bgcolor=bg, font=dict(color="#1a0f2e", family="Inter"), legend=dict(bgcolor="#ece3f8"), margin=dict(t=20,b=20))
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Detailed Results")
    details = results["details"]
    tab_f, tab_a, tab_b = st.tabs(["Factual", "Adversarial", "Bias"])
    def build_df(cat, key):
        oss_rows = {r["prompt_id"]:r for r in details["oss"]      if r["category"]==cat}
        ft_rows  = {r["prompt_id"]:r for r in details["frontier"] if r["category"]==cat}
        rows = []
        for pid in oss_rows:
            or_=oss_rows[pid]; fr=ft_rows.get(pid,{})
            rows.append({"ID":pid,"Prompt":or_["prompt"][:60]+"...",f"OSS {key}":or_.get(key,"-"),f"Frontier {key}":fr.get(key,"-"),"OSS note":or_.get("explanation","")[:80],"Frontier note":fr.get("explanation","")[:80]})
        return pd.DataFrame(rows)
    with tab_f: st.dataframe(build_df("factual",     "accuracy_score"),  use_container_width=True)
    with tab_a: st.dataframe(build_df("adversarial", "safety_score"),    use_container_width=True)
    with tab_b: st.dataframe(build_df("bias",        "neutrality_score"),use_container_width=True)

    st.markdown("#### Export")
    import json as _j
    st.download_button("Download full results (JSON)", data=_j.dumps(results,indent=2), file_name="eval_results.json", mime="application/json")


# ── Nav panel ──────────────────────────────────────────────────────────────────

NAV_ITEMS = [
    ("oss",      "OSS Assistant"),
    ("frontier", "Frontier Assistant"),
    ("compare",  "Side-by-Side"),
    ("evaluate", "Evaluate"),
]

def render_nav():
    active = st.session_state.active_page
    api_ok = bool(st.session_state.groq_key)
    dot_color = "#7de88a" if api_ok else "#e87d7d"

    # Logo
    st.markdown("""
    <div style="font-size:21px;font-weight:700;color:#ffffff;letter-spacing:-0.4px;margin-bottom:20px;padding-top:4px;">
        Eval<span style="color:#c0a0e0;">Lab</span>
    </div>
    """, unsafe_allow_html=True)

    # Status card
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.1);border-radius:10px;padding:10px 14px;margin-bottom:4px;">
        <div style="font-size:10px;color:rgba(255,255,255,0.4);font-weight:600;letter-spacing:1px;text-transform:uppercase;margin-bottom:5px;">API Status</div>
        <div style="font-size:12.5px;color:rgba(255,255,255,0.85);display:flex;align-items:center;gap:7px;">
            <span style="width:8px;height:8px;border-radius:50%;background:{dot_color};flex-shrink:0;"></span>
            {"Groq connected" if api_ok else "No API key — check .env"}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Divider + section label
    st.markdown("""
    <hr style="border:none;border-top:1px solid rgba(255,255,255,0.12);margin:16px 0 10px;">
    <div style="font-size:10px;font-weight:600;color:rgba(255,255,255,0.35);letter-spacing:1.2px;text-transform:uppercase;padding:0 4px;margin-bottom:6px;">
        Navigation
    </div>
    """, unsafe_allow_html=True)

    # Nav buttons — rendered as Streamlit buttons so they work inside the styled column
    for page_id, label in NAV_ITEMS:
        is_active = active == page_id
        display = f"▸  {label}" if is_active else f"    {label}"
        if st.button(display, key=f"nav_{page_id}", use_container_width=True):
            st.session_state.active_page = page_id
            st.rerun()

    # Bottom info
    st.markdown("""
    <hr style="border:none;border-top:1px solid rgba(255,255,255,0.12);margin:20px 0 12px;">
    <div style="font-size:11px;color:rgba(255,255,255,0.3);line-height:2;">
        <span style="color:rgba(255,255,255,0.5);font-weight:600;font-size:10.5px;">Models</span><br>
        OSS · llama-3.1-8b-instant<br>
        Frontier · llama-3.3-70b<br>
        <br>
        <span style="color:rgba(255,255,255,0.5);font-weight:600;font-size:10.5px;">Tools</span><br>
        Calculator · DateTime · Web Search<br>
        <br>
        <span style="color:rgba(255,255,255,0.5);font-weight:600;font-size:10.5px;">Safety</span><br>
        Input + output guardrails<br>
        JSONL observability logging
    </div>
    """, unsafe_allow_html=True)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    init_session()

    nav_col, main_col = st.columns([1.4, 5.6], gap="medium")

    with nav_col:
        render_nav()

    with main_col:
        page = st.session_state.active_page
        if   page == "oss":      page_chat("oss",      "OSS Assistant",      "Llama 3.1-8B Instant via Groq — small, fast open-source model")
        elif page == "frontier": page_chat("frontier",  "Frontier Assistant", "Llama 3.3-70B Versatile via Groq — large frontier-class model")
        elif page == "compare":  page_compare()
        elif page == "evaluate": page_evaluate()


if __name__ == "__main__":
    main()
