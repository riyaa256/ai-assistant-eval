"""
AI Assistant Evaluation Platform
Streamlit UI for OSS (Qwen2.5) vs Frontier (Gemini) comparison.
"""

import os
import time
import uuid

from dotenv import load_dotenv
load_dotenv()

import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Assistant Eval Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Global */
[data-testid="stAppViewContainer"] { background: #0f1117; }
[data-testid="stSidebar"] { background: #1a1d27; }
h1, h2, h3, h4 { color: #e8eaf6; }

/* Chat bubbles */
.user-bubble {
    background: linear-gradient(135deg, #5c6bc0 0%, #7e57c2 100%);
    color: white;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 16px;
    margin: 6px 0;
    margin-left: 20%;
    word-break: break-word;
}
.assistant-bubble {
    background: #1e2130;
    color: #e0e0e0;
    border: 1px solid #2d3250;
    border-radius: 18px 18px 18px 4px;
    padding: 12px 16px;
    margin: 6px 0;
    margin-right: 20%;
    word-break: break-word;
    white-space: pre-wrap;
}
.meta-tag {
    font-size: 11px;
    color: #8892a4;
    margin-top: 4px;
    margin-bottom: 10px;
}
.tool-badge {
    background: #263238;
    border: 1px solid #37474f;
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 11px;
    color: #80cbc4;
    display: inline-block;
    margin: 2px 3px;
}
.guard-badge {
    background: #b71c1c22;
    border: 1px solid #b71c1c;
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 11px;
    color: #ef9a9a;
    display: inline-block;
}
/* Metric cards */
.metric-card {
    background: #1a1d27;
    border: 1px solid #2d3250;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
}
.metric-value { font-size: 28px; font-weight: 700; color: #7986cb; }
.metric-label { font-size: 12px; color: #8892a4; margin-top: 4px; }
/* Input */
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
    background: #1e2130;
    color: #e0e0e0;
    border: 1px solid #2d3250;
    border-radius: 10px;
}
/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #5c6bc0, #7e57c2);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


# ── Session state helpers ──────────────────────────────────────────────────────

def init_session():
    defaults = {
        "session_id": str(uuid.uuid4())[:8],
        "oss_messages": [],       # list of (role, content, meta)
        "frontier_messages": [],
        "compare_pairs": [],      # list of (prompt, oss_resp, oss_meta, frontier_resp, frontier_meta)
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
        assistant = OSSAssistant(groq_api_key=key)
        assistant.set_session_id(st.session_state.session_id)
        st.session_state.oss_assistant = assistant
    return st.session_state.oss_assistant


def get_or_create_frontier():
    key = st.session_state.groq_key
    if not key:
        return None
    if st.session_state.frontier_assistant is None:
        from src.assistants.frontier_assistant import FrontierAssistant
        assistant = FrontierAssistant(groq_api_key=key)
        assistant.set_session_id(st.session_state.session_id)
        st.session_state.frontier_assistant = assistant
    return st.session_state.frontier_assistant


# ── UI helpers ─────────────────────────────────────────────────────────────────

def render_message(role: str, content: str, meta: dict):
    if role == "user":
        st.markdown(f'<div class="user-bubble">{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="assistant-bubble">{content}</div>',
            unsafe_allow_html=True,
        )
        parts = []
        if "latency_ms" in meta:
            parts.append(f"⏱ {meta['latency_ms']:.0f}ms")
        if "input_tokens" in meta and "output_tokens" in meta:
            parts.append(f"🔢 {meta['input_tokens']}↑ {meta['output_tokens']}↓ tokens")
        if meta.get("tool_calls"):
            for tc in meta["tool_calls"]:
                parts.append(f'<span class="tool-badge">🔧 {tc["name"]}</span>')
        if meta.get("guardrail_blocked"):
            parts.append('<span class="guard-badge">🛡 guardrail blocked</span>')
        if meta.get("output_filtered"):
            parts.append('<span class="guard-badge">🛡 output filtered</span>')
        if parts:
            st.markdown(
                f'<div class="meta-tag">{" &nbsp;|&nbsp; ".join(parts)}</div>',
                unsafe_allow_html=True,
            )


def chat_tab(assistant_key: str, title: str, color: str):
    """Render a single-assistant chat tab."""
    assistant = get_or_create_oss() if assistant_key == "oss" else get_or_create_frontier()
    messages_key = f"{assistant_key}_messages"

    st.markdown(f"## {title}")

    if assistant is None:
        token_name = "Groq API Key"
        st.warning(f"⚠️ Please enter your {token_name} in the sidebar to start chatting.")
        return

    # Render history
    for role, content, meta in st.session_state[messages_key]:
        render_message(role, content, meta)

    # Input area
    with st.form(key=f"chat_form_{assistant_key}", clear_on_submit=True):
        cols = st.columns([8, 1])
        user_input = cols[0].text_input(
            "Message", placeholder="Ask anything…", label_visibility="collapsed"
        )
        submitted = cols[1].form_submit_button("Send")

    col_clear, _ = st.columns([1, 5])
    if col_clear.button("🗑 Clear", key=f"clear_{assistant_key}"):
        st.session_state[messages_key] = []
        assistant.clear_history()
        st.rerun()

    if submitted and user_input.strip():
        st.session_state[messages_key].append(("user", user_input.strip(), {}))
        with st.spinner("Thinking…"):
            response, meta = assistant.chat(user_input.strip())
        st.session_state[messages_key].append(("assistant", response, meta))
        st.rerun()

    # Stats in expander
    with st.expander("📊 Session metrics"):
        stats = assistant.get_stats()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Requests", stats.get("total_requests", 0))
        c2.metric("Avg latency", f"{stats.get('avg_latency_ms', 0):.0f}ms")
        c3.metric("Total tokens", stats.get("total_input_tokens", 0) + stats.get("total_output_tokens", 0))
        c4.metric("Guardrail hits", stats.get("guardrail_triggers", 0))


def compare_tab():
    st.markdown("## ⚡ Side-by-Side Comparison")

    oss = get_or_create_oss()
    frontier = get_or_create_frontier()

    if oss is None or frontier is None:
        st.warning("⚠️ Both API keys are required for comparison.")
        return

    with st.form("compare_form", clear_on_submit=True):
        query = st.text_area(
            "Enter a prompt to send to both assistants simultaneously",
            placeholder="e.g. 'What is quantum entanglement?' or 'Write me a haiku about the ocean'",
            height=80,
        )
        submitted = st.form_submit_button("🚀 Compare Both")

    if submitted and query.strip():
        with st.spinner("Querying both assistants…"):
            col1, col2 = st.columns(2)
            oss_resp = oss_meta = frontier_resp = frontier_meta = None

            # Run in sequence (parallel would require threading)
            t0 = time.time()
            oss_resp, oss_meta = oss.chat(query.strip())
            oss.clear_history()
            frontier_resp, frontier_meta = frontier.chat(query.strip())
            frontier.clear_history()

        st.session_state.compare_pairs.insert(0, (
            query.strip(), oss_resp, oss_meta, frontier_resp, frontier_meta
        ))

    # Render comparison history
    for prompt, oss_r, oss_m, ft_r, ft_m in st.session_state.compare_pairs:
        with st.container():
            st.markdown(
                f'<div class="user-bubble" style="margin-left:0;margin-right:0">{prompt}</div>',
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**🔵 Llama 3.1-8B (OSS)**")
                render_message("assistant", oss_r, oss_m)
            with c2:
                st.markdown("**🟣 Llama 3.3-70B (Frontier)**")
                render_message("assistant", ft_r, ft_m)

            # Quick delta
            oss_lat = oss_m.get("latency_ms", 0)
            ft_lat = ft_m.get("latency_ms", 0)
            faster = "Llama 3.1-8B" if oss_lat < ft_lat else "Llama 3.3-70B"
            st.caption(
                f"Latency — 8B: {oss_lat:.0f}ms · 70B: {ft_lat:.0f}ms · "
                f"{faster} was faster by {abs(oss_lat - ft_lat):.0f}ms"
            )
            st.divider()


def eval_tab():
    import plotly.graph_objects as go
    import plotly.express as px
    import pandas as pd

    st.markdown("## 📊 Evaluation Dashboard")
    st.markdown(
        "Runs **30 structured test prompts** across factual accuracy, adversarial/jailbreak "
        "resistance, and bias/fairness. Uses Llama 3.3-70B as an LLM judge to score every response."
    )

    frontier = get_or_create_frontier()
    oss = get_or_create_oss()

    if frontier is None or oss is None:
        st.warning("⚠️ Both API keys are required to run the evaluation.")
        return

    if st.button("▶️ Run Full Evaluation (~5-8 minutes)"):
        from src.evaluation.eval_suite import EvalSuite

        suite = EvalSuite(
            oss_assistant=oss,
            frontier_assistant=frontier,
            groq_api_key=st.session_state.groq_key,
        )

        progress_bar = st.progress(0.0)
        status_text = st.empty()

        def cb(frac: float, label: str):
            progress_bar.progress(frac)
            status_text.text(f"Evaluating: {label}")

        with st.spinner("Running evaluation…"):
            results = suite.run(progress_cb=cb)

        progress_bar.progress(1.0)
        status_text.text("✅ Evaluation complete!")
        st.session_state.eval_results = results
        st.rerun()

    results = st.session_state.eval_results
    if results is None:
        st.info("Click **Run Full Evaluation** to start.")
        return

    summary = results["summary"]
    oss_s = summary["oss"]
    ft_s = summary["frontier"]

    # ── Overview metrics ──────────────────────────────────────────────────────
    st.markdown("### Overall Comparison")
    cols = st.columns(6)
    metrics = [
        ("Hallucination Rate", f"{oss_s['hallucination_rate']:.0%}", f"{ft_s['hallucination_rate']:.0%}"),
        ("Avg Accuracy", f"{oss_s['avg_accuracy']:.1f}/10", f"{ft_s['avg_accuracy']:.1f}/10"),
        ("Jailbreak Rate", f"{oss_s['jailbreak_rate']:.0%}", f"{ft_s['jailbreak_rate']:.0%}"),
        ("Avg Safety", f"{oss_s['avg_safety_score']:.1f}/10", f"{ft_s['avg_safety_score']:.1f}/10"),
        ("Bias Rate", f"{oss_s['bias_rate']:.0%}", f"{ft_s['bias_rate']:.0%}"),
        ("Avg Neutrality", f"{oss_s['avg_neutrality']:.1f}/10", f"{ft_s['avg_neutrality']:.1f}/10"),
    ]
    for i, (label, oss_v, ft_v) in enumerate(metrics):
        with cols[i]:
            st.metric(f"OSS — {label}", oss_v)
            st.metric(f"Frontier — {label}", ft_v)

    # ── Radar chart ───────────────────────────────────────────────────────────
    st.markdown("### Performance Radar")
    categories = ["Accuracy", "Safety", "Neutrality"]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[oss_s["avg_accuracy"], oss_s["avg_safety_score"], oss_s["avg_neutrality"]],
        theta=categories, fill="toself", name="Llama 3.1-8B (OSS)",
        line_color="#5c6bc0",
    ))
    fig.add_trace(go.Scatterpolar(
        r=[ft_s["avg_accuracy"], ft_s["avg_safety_score"], ft_s["avg_neutrality"]],
        theta=categories, fill="toself", name="Llama 3.3 (Frontier)",
        line_color="#7e57c2",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
        paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
        font_color="#e0e0e0", legend_bgcolor="#1a1d27",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Grouped bar chart ─────────────────────────────────────────────────────
    st.markdown("### Category Scores")
    bar_df = pd.DataFrame({
        "Category": ["Accuracy (F)", "Safety (A)", "Neutrality (B)"] * 2,
        "Score": [
            oss_s["avg_accuracy"], oss_s["avg_safety_score"], oss_s["avg_neutrality"],
            ft_s["avg_accuracy"], ft_s["avg_safety_score"], ft_s["avg_neutrality"],
        ],
        "Model": ["Llama 3.1-8B"] * 3 + ["Llama 3.3-70B"] * 3,
    })
    fig2 = px.bar(
        bar_df, x="Category", y="Score", color="Model", barmode="group",
        color_discrete_map={"Llama 3.1-8B": "#5c6bc0", "Llama 3.3-70B": "#7e57c2"},
        range_y=[0, 10],
    )
    fig2.update_layout(paper_bgcolor="#0f1117", plot_bgcolor="#1a1d27", font_color="#e0e0e0")
    st.plotly_chart(fig2, use_container_width=True)

    # ── Detailed results table ────────────────────────────────────────────────
    st.markdown("### Detailed Results")
    details = results["details"]

    tab_f, tab_a, tab_b = st.tabs(["Factual", "Adversarial", "Bias"])

    def build_df(category: str, oss_key: str, ft_key: str) -> pd.DataFrame:
        oss_rows = {r["prompt_id"]: r for r in details["oss"] if r["category"] == category}
        ft_rows = {r["prompt_id"]: r for r in details["frontier"] if r["category"] == category}
        rows = []
        for pid in oss_rows:
            or_ = oss_rows[pid]
            fr = ft_rows.get(pid, {})
            rows.append({
                "ID": pid,
                "Prompt": or_["prompt"][:60] + "…",
                f"OSS {oss_key}": or_.get(oss_key, "–"),
                f"Frontier {oss_key}": fr.get(oss_key, "–"),
                "OSS Note": or_.get("explanation", "")[:80],
                "Frontier Note": fr.get("explanation", "")[:80],
            })
        return pd.DataFrame(rows)

    with tab_f:
        st.dataframe(build_df("factual", "accuracy_score", "accuracy_score"), use_container_width=True)
    with tab_a:
        st.dataframe(build_df("adversarial", "safety_score", "safety_score"), use_container_width=True)
    with tab_b:
        st.dataframe(build_df("bias", "neutrality_score", "neutrality_score"), use_container_width=True)

    # ── Download report ───────────────────────────────────────────────────────
    st.markdown("### Export")
    import json as _json
    report_json = _json.dumps(results, indent=2)
    st.download_button(
        "⬇️ Download Full Results (JSON)",
        data=report_json,
        file_name="eval_results.json",
        mime="application/json",
    )


# ── Sidebar ────────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("## 🤖 AI Assistant Eval")
        st.markdown("*OSS · Frontier · Evaluation*")
        st.divider()

        st.markdown("### 🔑 API Keys")
        st.caption("Keys are loaded from your `.env` file — never entered in the UI.")
        if st.session_state.groq_key:
            st.success("✅ Groq API Key — loaded (used by both models)")
        else:
            st.error("❌ GROQ_API_KEY missing from .env")

        st.divider()
        st.markdown("### 📋 Models")
        st.markdown("**OSS:** `llama-3.1-8b-instant` (Groq)")
        st.markdown("**Frontier:** `llama-3.3-70b-versatile` (Groq)")

        st.divider()
        st.markdown("### 🛡 Guardrails")
        st.markdown(
            "Both assistants have **input + output guardrails**.\n"
            "OSS additionally uses a regex-based output filter.\n"
            "Triggered events are logged to `logs/`."
        )

        st.divider()
        st.markdown("### 🔧 Tools")
        st.markdown("• Calculator\n• Date / Time\n• Web Search (DuckDuckGo)")



# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    init_session()
    render_sidebar()

    tab_oss, tab_frontier, tab_compare, tab_eval = st.tabs([
        "🔵 OSS Assistant (Llama 3.1-8B)",
        "🟣 Frontier Assistant (Llama 3.3)",
        "⚡ Side-by-Side",
        "📊 Evaluate",
    ])

    with tab_oss:
        chat_tab("oss", "🔵 Llama 3.1-8B Instant", "#5c6bc0")
    with tab_frontier:
        chat_tab("frontier", "🟣 Llama 3.3-70B (Groq)", "#7e57c2")
    with tab_compare:
        compare_tab()
    with tab_eval:
        eval_tab()


if __name__ == "__main__":
    main()
