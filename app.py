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
[data-testid="stMain"] { background: #bfadd6 !important; }

.block-container {
    padding: 16px !important;
    max-width: 100% !important;
}

/* ── NAV column ── */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child,
[data-testid="stColumns"] > [data-testid="stColumn"]:first-child {
    background: #38265a !important;
    border-radius: 20px !important;
    padding: 28px 18px 24px !important;
    min-height: calc(100vh - 40px) !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child > div,
[data-testid="stColumns"] > [data-testid="stColumn"]:first-child > div {
    gap: 0 !important;
}

/* Remove link underlines globally */
a { text-decoration: none !important; }

/* ── ALL buttons — clean light style ── */
.stButton > button {
    background: #e8ddf5 !important;
    color: #2d1a50 !important;
    border: 1px solid #cdbde8 !important;
    border-radius: 11px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 9px 18px !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
    width: auto !important;
}
.stButton > button:hover {
    background: #dccff0 !important;
    border-color: #b8a0d8 !important;
    color: #1a0a38 !important;
}

/* Primary action buttons (Send, Compare) */
[data-testid="stFormSubmitButton"] > button {
    background: #5c3d88 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 11px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 9px 22px !important;
    box-shadow: 0 3px 10px rgba(70, 30, 130, 0.28) !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    background: #4d3075 !important;
    box-shadow: 0 4px 14px rgba(70, 30, 130, 0.38) !important;
}

/* ── Main column padding ── */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2),
[data-testid="stColumns"] > [data-testid="stColumn"]:nth-child(2) {
    padding: 8px 8px 8px 8px !important;
}

/* ── Page header ── */
.page-title {
    font-size: 30px;
    font-weight: 700;
    color: #1a0a38;
    letter-spacing: -0.7px;
    line-height: 1.2;
    margin: 4px 0 6px 0;
}
.page-subtitle {
    font-size: 13px;
    color: #6b52a0;
    margin: 0 0 26px 0;
    font-weight: 400;
}

/* ── Chat bubbles ── */
.user-bubble {
    background: #5c3d88;
    color: #ffffff;
    border-radius: 18px 18px 5px 18px;
    padding: 12px 18px;
    margin: 10px 0 4px 18%;
    font-size: 14px;
    line-height: 1.6;
    word-break: break-word;
    box-shadow: 0 3px 12px rgba(70, 30, 130, 0.22);
}
.assistant-bubble {
    background: #ffffff;
    color: #1a0a38;
    border: 1px solid #d8ccec;
    border-radius: 18px 18px 18px 5px;
    padding: 12px 18px;
    margin: 4px 18% 4px 0;
    font-size: 14px;
    line-height: 1.6;
    word-break: break-word;
    white-space: pre-wrap;
    box-shadow: 0 2px 8px rgba(70, 30, 130, 0.08);
}
.meta-row {
    font-size: 11.5px;
    color: #9880c0;
    margin: 2px 0 14px 4px;
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
}
.tool-pill {
    background: #ede5f8;
    color: #4a2d80;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 500;
    border: 1px solid #d0c0ec;
}
.guard-pill {
    background: #fde8e8;
    color: #a03030;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 500;
}
.card-label {
    font-size: 10.5px;
    font-weight: 700;
    color: #8060b0;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
}

/* ── Inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: #ffffff !important;
    color: #1a0a38 !important;
    border: 1.5px solid #c8b8e4 !important;
    border-radius: 12px !important;
    font-size: 14px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #7040b8 !important;
    box-shadow: 0 0 0 3px rgba(100, 50, 180, 0.1) !important;
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder { color: #b0a0cc !important; }

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: #ffffff;
    border-radius: 14px;
    padding: 14px 16px;
    border: 1px solid #d8ccec;
    box-shadow: 0 2px 8px rgba(70, 30, 130, 0.06);
}
[data-testid="stMetricLabel"] p  { color: #7060a0 !important; font-size: 12px !important; }
[data-testid="stMetricValue"]    { color: #1a0a38 !important; font-weight: 700 !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #f0e8f8 !important;
    border: 1px solid #d8ccec !important;
    border-radius: 14px !important;
}
[data-testid="stExpander"] summary {
    color: #4a2d80 !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}

/* ── Tabs ── */
[data-baseweb="tab-list"] { background: transparent !important; gap: 4px; }
[data-baseweb="tab"] {
    color: #7060a0 !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 8px 16px !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    color: #38265a !important;
    font-weight: 700 !important;
    border-bottom: 2px solid #5c3d88 !important;
    background: transparent !important;
}

/* ── Progress ── */
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #5c3d88, #9060c8) !important;
    border-radius: 6px;
}

/* ── Misc ── */
[data-testid="stDataFrame"] { border-radius: 12px !important; }
[data-testid="stAlert"]     { border-radius: 12px !important; }
hr { border-color: #d0c0e4 !important; margin: 20px 0 !important; }

[data-testid="stDownloadButton"] > button {
    background: #f0e8f8 !important;
    color: #38265a !important;
    border: 1px solid #c8b8e4 !important;
    border-radius: 11px !important;
    font-weight: 600 !important;
    box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)


# ── Session ────────────────────────────────────────────────────────────────────

def init_session():
    defaults = {
        "session_id":        str(uuid.uuid4())[:8],
        "oss_messages":      [],
        "frontier_messages": [],
        "compare_pairs":     [],
        "eval_results":      None,
        "oss_assistant":     None,
        "frontier_assistant":None,
        "groq_key":          os.getenv("GROQ_API_KEY", ""),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def get_active_page() -> str:
    return st.query_params.get("page", "oss")


def get_or_create_oss():
    key = st.session_state.groq_key
    if not key: return None
    if st.session_state.oss_assistant is None:
        from src.assistants.oss_assistant import OSSAssistant
        a = OSSAssistant(groq_api_key=key)
        a.set_session_id(st.session_state.session_id)
        st.session_state.oss_assistant = a
    return st.session_state.oss_assistant


def get_or_create_frontier():
    key = st.session_state.groq_key
    if not key: return None
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
    if "latency_ms"    in meta: parts.append(f"{meta['latency_ms']:.0f} ms")
    if "input_tokens"  in meta: parts.append(f"{meta['input_tokens']} in / {meta['output_tokens']} out")
    for tc in meta.get("tool_calls") or []:
        parts.append(f'<span class="tool-pill">{tc["name"]}</span>')
    if meta.get("guardrail_blocked"):  parts.append('<span class="guard-pill">guardrail blocked</span>')
    if meta.get("output_filtered"):    parts.append('<span class="guard-pill">output filtered</span>')
    if parts:
        st.markdown(
            '<div class="meta-row">' +
            ' <span style="color:#c8b8e0">·</span> '.join(parts) +
            '</div>',
            unsafe_allow_html=True,
        )


# ── Nav ────────────────────────────────────────────────────────────────────────

NAV_ITEMS = [
    ("oss",      "OSS Assistant"),
    ("frontier", "Frontier Assistant"),
    ("compare",  "Side-by-Side"),
    ("evaluate", "Evaluate"),
]

def render_nav(active: str):
    api_ok = bool(st.session_state.groq_key)
    dot_c  = "#6edd7a" if api_ok else "#f08080"
    status = "Groq connected" if api_ok else "No API key — check .env"

    # Build nav link HTML
    links_html = ""
    for page_id, label in NAV_ITEMS:
        is_active = active == page_id
        if is_active:
            item_style = (
                "background:rgba(255,255,255,0.16);"
                "color:#ffffff;"
                "font-weight:600;"
            )
            prefix = "&#9656;&nbsp;&nbsp;"
        else:
            item_style = "color:rgba(255,255,255,0.6);"
            prefix = "&nbsp;&nbsp;&nbsp;&nbsp;"
        links_html += f"""
        <a href="?page={page_id}"
           style="display:block;{item_style}padding:10px 14px;border-radius:10px;
                  font-size:13.5px;margin-bottom:3px;letter-spacing:0.1px;
                  transition:background 0.15s,color 0.15s;"
           onmouseover="this.style.background='rgba(255,255,255,0.1)';this.style.color='#fff';"
           onmouseout="this.style.background={'rgba(255,255,255,0.16)' if is_active else 'transparent'};
                       this.style.color={'#fff' if is_active else 'rgba(255,255,255,0.6)'};">
            {prefix}{label}
        </a>"""

    st.markdown(f"""
    <style>a:hover {{text-decoration:none !important;}}</style>

    <!-- Logo -->
    <div style="font-size:22px;font-weight:700;color:#fff;letter-spacing:-0.5px;margin-bottom:24px;padding-top:2px;">
        Eval<span style="color:#b898e0;">Lab</span>
    </div>

    <!-- API Status -->
    <div style="background:rgba(255,255,255,0.1);border-radius:12px;padding:12px 14px;margin-bottom:6px;">
        <div style="font-size:10px;color:rgba(255,255,255,0.4);font-weight:700;
                    letter-spacing:1.1px;text-transform:uppercase;margin-bottom:7px;">
            API Status
        </div>
        <div style="display:flex;align-items:center;gap:8px;font-size:13px;color:rgba(255,255,255,0.9);">
            <span style="width:8px;height:8px;border-radius:50%;background:{dot_c};
                         flex-shrink:0;display:inline-block;
                         box-shadow:0 0 6px {dot_c};"></span>
            {status}
        </div>
    </div>

    <!-- Nav section -->
    <div style="height:1px;background:rgba(255,255,255,0.1);margin:18px 0 12px;"></div>
    <div style="font-size:10px;font-weight:700;color:rgba(255,255,255,0.3);
                letter-spacing:1.3px;text-transform:uppercase;padding:0 4px;margin-bottom:8px;">
        Navigation
    </div>

    {links_html}

    <!-- Info footer -->
    <div style="height:1px;background:rgba(255,255,255,0.1);margin:20px 0 14px;"></div>
    <div style="font-size:11px;color:rgba(255,255,255,0.28);line-height:2.1;">
        <span style="color:rgba(255,255,255,0.5);font-weight:700;font-size:10.5px;
                     text-transform:uppercase;letter-spacing:0.8px;">Models</span><br>
        OSS&nbsp;·&nbsp;llama-3.1-8b-instant<br>
        Frontier&nbsp;·&nbsp;llama-3.3-70b<br>
        <br>
        <span style="color:rgba(255,255,255,0.5);font-weight:700;font-size:10.5px;
                     text-transform:uppercase;letter-spacing:0.8px;">Tools</span><br>
        Calculator&nbsp;·&nbsp;DateTime&nbsp;·&nbsp;Web Search<br>
        <br>
        <span style="color:rgba(255,255,255,0.5);font-weight:700;font-size:10.5px;
                     text-transform:uppercase;letter-spacing:0.8px;">Safety</span><br>
        Input&nbsp;+&nbsp;output guardrails<br>
        JSONL observability logging
    </div>
    """, unsafe_allow_html=True)


# ── Pages ──────────────────────────────────────────────────────────────────────

def page_chat(assistant_key: str, title: str, subtitle: str):
    assistant   = get_or_create_oss() if assistant_key == "oss" else get_or_create_frontier()
    messages_key = f"{assistant_key}_messages"

    st.markdown(f'<p class="page-title">{title}</p><p class="page-subtitle">{subtitle}</p>',
                unsafe_allow_html=True)

    if assistant is None:
        st.warning("Groq API key not found. Check your .env file.")
        return

    for role, content, meta in st.session_state[messages_key]:
        render_message(role, content, meta)

    with st.form(key=f"form_{assistant_key}", clear_on_submit=True):
        cols = st.columns([10, 1.6])
        user_input = cols[0].text_input(
            "msg", placeholder="Ask anything...", label_visibility="collapsed"
        )
        submitted = cols[1].form_submit_button("Send")

    c1, _ = st.columns([2, 8])
    with c1:
        if st.button("Clear history", key=f"clear_{assistant_key}"):
            st.session_state[messages_key] = []
            assistant.clear_history()
            st.rerun()

    if submitted and user_input.strip():
        st.session_state[messages_key].append(("user", user_input.strip(), {}))
        with st.spinner("Thinking..."):
            response, meta = assistant.chat(user_input.strip())
        st.session_state[messages_key].append(("assistant", response, meta))
        st.rerun()

    with st.expander("Session metrics"):
        stats = assistant.get_stats()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Requests",       stats.get("total_requests", 0))
        c2.metric("Avg latency",    f"{stats.get('avg_latency_ms', 0):.0f} ms")
        c3.metric("Tokens used",    stats.get("total_input_tokens", 0) + stats.get("total_output_tokens", 0))
        c4.metric("Guardrail hits", stats.get("guardrail_triggers", 0))


def page_compare():
    st.markdown(
        '<p class="page-title">Side-by-Side</p>'
        '<p class="page-subtitle">Send one prompt to both models and compare responses instantly</p>',
        unsafe_allow_html=True,
    )

    oss      = get_or_create_oss()
    frontier = get_or_create_frontier()
    if oss is None or frontier is None:
        st.warning("Groq API key is required. Check your .env file.")
        return

    with st.form("compare_form", clear_on_submit=True):
        query = st.text_area(
            "prompt",
            placeholder="e.g. Explain quantum entanglement in simple terms...",
            height=90,
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Compare both models")

    if submitted and query.strip():
        with st.spinner("Querying both models..."):
            oss_resp, oss_meta         = oss.chat(query.strip());      oss.clear_history()
            frontier_resp, frontier_meta = frontier.chat(query.strip()); frontier.clear_history()
        st.session_state.compare_pairs.insert(
            0, (query.strip(), oss_resp, oss_meta, frontier_resp, frontier_meta)
        )

    for prompt, oss_r, oss_m, ft_r, ft_m in st.session_state.compare_pairs:
        st.markdown(
            f'<div class="user-bubble" style="margin-left:0;margin-right:0;border-radius:14px;">'
            f'{prompt}</div>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="card-label">Llama 3.1 · 8B · OSS</div>', unsafe_allow_html=True)
            render_message("assistant", oss_r, oss_m)
        with c2:
            st.markdown('<div class="card-label">Llama 3.3 · 70B · Frontier</div>', unsafe_allow_html=True)
            render_message("assistant", ft_r, ft_m)
        oss_lat = oss_m.get("latency_ms", 0)
        ft_lat  = ft_m.get("latency_ms",  0)
        faster  = "8B" if oss_lat < ft_lat else "70B"
        st.caption(
            f"8B: {oss_lat:.0f} ms  ·  70B: {ft_lat:.0f} ms  ·  "
            f"{faster} was faster by {abs(oss_lat - ft_lat):.0f} ms"
        )
        st.divider()


def page_evaluate():
    import plotly.graph_objects as go
    import plotly.express as px
    import pandas as pd

    st.markdown(
        '<p class="page-title">Evaluation Dashboard</p>'
        '<p class="page-subtitle">'
        '30 structured prompts — factual accuracy, adversarial safety, bias fairness'
        '&nbsp;·&nbsp;judge: Llama 3.3-70B'
        '</p>',
        unsafe_allow_html=True,
    )

    oss      = get_or_create_oss()
    frontier = get_or_create_frontier()
    if oss is None or frontier is None:
        st.warning("Groq API key is required. Check your .env file.")
        return

    if st.button("Run Full Evaluation  (approx. 5-8 minutes)"):
        from src.evaluation.eval_suite import EvalSuite
        suite = EvalSuite(
            oss_assistant=oss, frontier_assistant=frontier,
            groq_api_key=st.session_state.groq_key,
        )
        pb, status = st.progress(0.0), st.empty()
        def cb(f, l): pb.progress(f); status.text(f"Evaluating: {l}")
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
    bg    = "#ffffff"

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

    st.markdown("#### Performance Radar")
    cats = ["Accuracy", "Safety", "Neutrality"]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[oss_s["avg_accuracy"], oss_s["avg_safety_score"], oss_s["avg_neutrality"]],
        theta=cats, fill="toself", name="Llama 3.1-8B (OSS)", line_color="#5c3d88",
    ))
    fig.add_trace(go.Scatterpolar(
        r=[ft_s["avg_accuracy"],  ft_s["avg_safety_score"],  ft_s["avg_neutrality"]],
        theta=cats, fill="toself", name="Llama 3.3-70B (Frontier)", line_color="#9060c8",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 10], gridcolor="#e0d4f4", color="#7060a0"),
            bgcolor=bg,
        ),
        paper_bgcolor=bg, plot_bgcolor=bg,
        font=dict(color="#1a0a38", family="Inter"),
        legend=dict(bgcolor="#f0e8f8", bordercolor="#d8ccec", borderwidth=1),
        margin=dict(t=30, b=20, l=20, r=20),
    )
    st.plotly_chart(fig, use_container_width=True)

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
        color_discrete_map={"Llama 3.1-8B": "#5c3d88", "Llama 3.3-70B": "#9060c8"},
        range_y=[0, 10],
    )
    fig2.update_layout(
        paper_bgcolor=bg, plot_bgcolor=bg,
        font=dict(color="#1a0a38", family="Inter"),
        legend=dict(bgcolor="#f0e8f8"),
        margin=dict(t=20, b=20),
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Detailed Results")
    details = results["details"]
    tab_f, tab_a, tab_b = st.tabs(["Factual", "Adversarial", "Bias"])

    def build_df(cat, key):
        oss_rows = {r["prompt_id"]: r for r in details["oss"]      if r["category"] == cat}
        ft_rows  = {r["prompt_id"]: r for r in details["frontier"] if r["category"] == cat}
        rows = []
        for pid in oss_rows:
            or_ = oss_rows[pid]; fr = ft_rows.get(pid, {})
            rows.append({
                "ID": pid, "Prompt": or_["prompt"][:60] + "...",
                f"OSS {key}":      or_.get(key, "-"),
                f"Frontier {key}": fr.get(key, "-"),
                "OSS note":      or_.get("explanation", "")[:80],
                "Frontier note": fr.get("explanation", "")[:80],
            })
        return pd.DataFrame(rows)

    with tab_f: st.dataframe(build_df("factual",     "accuracy_score"),  use_container_width=True)
    with tab_a: st.dataframe(build_df("adversarial", "safety_score"),    use_container_width=True)
    with tab_b: st.dataframe(build_df("bias",        "neutrality_score"),use_container_width=True)

    st.markdown("#### Export")
    import json as _j
    st.download_button(
        "Download full results (JSON)",
        data=_j.dumps(results, indent=2),
        file_name="eval_results.json",
        mime="application/json",
    )


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    init_session()
    active = get_active_page()

    nav_col, main_col = st.columns([1.4, 5.6], gap="medium")

    with nav_col:
        render_nav(active)

    with main_col:
        if   active == "oss":      page_chat("oss",      "OSS Assistant",      "Llama 3.1-8B Instant via Groq — small, fast open-source model")
        elif active == "frontier": page_chat("frontier", "Frontier Assistant",  "Llama 3.3-70B Versatile via Groq — large frontier-class model")
        elif active == "compare":  page_compare()
        elif active == "evaluate": page_evaluate()


if __name__ == "__main__":
    main()
