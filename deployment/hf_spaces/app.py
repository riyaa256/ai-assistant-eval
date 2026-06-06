"""
HuggingFace Spaces deployment — Qwen2.5-0.5B-Instruct Personal Assistant
Includes: multi-turn memory, tools, guardrails, observability, safety layers.

Set the HF_TOKEN secret in your Space settings.
"""

import json
import os
import re
import time
from datetime import datetime, timezone

import gradio as gr
from huggingface_hub import InferenceClient

# ── Config ────────────────────────────────────────────────────────────────────
MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
HF_TOKEN = os.environ.get("HF_TOKEN", "")
MAX_TURNS = 15
MAX_TOKENS = 768

# Cost / latency reference table (shown in UI)
COST_TABLE = """
| Deployment Platform | Avg Latency | Cost / 1k tokens | Notes |
|---------------------|-------------|------------------|-------|
| HF Spaces (CPU free) | 3–8s | $0.00 | Shared, rate-limited |
| HF Spaces (ZeroGPU) | 0.8–2s | ~$0.001 | A100 bursts |
| Modal (A10G serverless) | 0.4–1.2s | ~$0.002 | Cold-start ~2s |
| RunPod (RTX 4090) | 0.3–0.9s | ~$0.003 | Persistent endpoint |
| Replicate | 1–3s | ~$0.002 | Easy deploy |
| Claude Sonnet (Frontier) | 1–3s | $0.003–$0.015 | Premium quality |
"""

# ── Guardrails ────────────────────────────────────────────────────────────────
BLOCKED_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"you\s+are\s+now\s+(DAN|jailbroken|unrestricted)",
    r"pretend\s+you\s+have\s+no\s+(restrictions|guidelines|safety)",
    r"how\s+to\s+(make|build)\s+(a\s+)?(bomb|explosive)",
    r"how\s+to\s+(make|synthesize)\s+(meth|cocaine|heroin)",
    r"child\s+(porn|sexual\s+abuse)",
    r"how\s+to\s+(kill|murder)\s+(someone|a\s+person)",
]


def is_safe_input(text: str) -> bool:
    t = text.lower()
    return not any(re.search(p, t) for p in BLOCKED_PATTERNS)


def is_safe_output(text: str) -> bool:
    t = text.lower()
    unsafe = [
        r"step.by.step\s+(instructions\s+)?(to\s+)?make\s+(a\s+)?(bomb|explosive)",
        r"synthesis\s+of\s+(cocaine|meth)",
    ]
    return not any(re.search(p, t) for p in unsafe)


# ── Tools ─────────────────────────────────────────────────────────────────────
def run_calculator(expression: str) -> str:
    import ast, operator as op
    OPS = {
        ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
        ast.Div: op.truediv, ast.Pow: op.pow, ast.USub: op.neg,
    }
    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp):
            return OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp):
            return OPS[type(node.op)](_eval(node.operand))
        raise ValueError("Unsupported")
    try:
        result = _eval(ast.parse(expression, mode="eval").body)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Calc error: {e}"


def get_datetime_tool(tz: str = "UTC") -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%A, %B %d, %Y at %I:%M %p UTC")


def web_search_tool(query: str) -> str:
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=2))
        if not results:
            return "No results found."
        return "\n\n".join(f"{r['title']}: {r['body']}" for r in results)
    except Exception as e:
        return f"Search unavailable: {e}"


TOOL_DESCRIPTIONS = """
## Tools

To call a tool, emit a fenced block:
```tool_call
{"name": "calculator", "arguments": {"expression": "sqrt(144)"}}
```

Available:
- **calculator** — evaluate math expressions
- **get_datetime** — get current date/time
- **web_search** — search the internet: `{"query": "..."}`
"""

SYSTEM_PROMPT = (
    "You are a helpful, harmless, and honest AI personal assistant. "
    "You maintain conversation context. "
    "Be accurate and admit uncertainty. "
    "Never produce harmful or biased content.\n\n"
    + TOOL_DESCRIPTIONS
)

# ── Observability ─────────────────────────────────────────────────────────────
request_log: list[dict] = []


def log_request(user_msg: str, response: str, latency_ms: float, tools_used: list):
    request_log.append({
        "ts": datetime.now(timezone.utc).isoformat(),
        "user": user_msg[:200],
        "response_length": len(response),
        "latency_ms": round(latency_ms, 1),
        "tools": tools_used,
    })


# ── Model inference ───────────────────────────────────────────────────────────
client = InferenceClient(token=HF_TOKEN) if HF_TOKEN else None


def _call_model(messages: list[dict], max_tokens: int = MAX_TOKENS) -> str:
    if client is None:
        return "Error: HF_TOKEN not set."
    response = client.chat_completion(
        model=MODEL_ID,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return response.choices[0].message.content or ""


def _parse_tool_call(text: str):
    m = re.search(r"```tool_call\s*\n(.*?)\n```", text, re.DOTALL)
    if m:
        try:
            d = json.loads(m.group(1))
            return d.get("name"), d.get("arguments", {})
        except Exception:
            pass
    return None, None


def execute_tool(name: str, args: dict) -> str:
    if name == "calculator":
        return run_calculator(args.get("expression", ""))
    if name == "get_datetime":
        return get_datetime_tool(args.get("timezone", "UTC"))
    if name == "web_search":
        return web_search_tool(args.get("query", ""))
    return f"Unknown tool: {name}"


# ── Chat function (called by Gradio) ─────────────────────────────────────────
def chat(user_message: str, history: list[list]):
    start = time.time()
    tools_used: list[str] = []

    if not user_message.strip():
        return "", history

    # Input guardrail
    if not is_safe_input(user_message):
        reply = "I'm sorry, I can't help with that request."
        history.append([user_message, reply])
        return "", history

    # Build messages from history
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for human, bot in (history or []):
        if human:
            messages.append({"role": "user", "content": human})
        if bot:
            messages.append({"role": "assistant", "content": bot})
    messages.append({"role": "user", "content": user_message})

    # Trim to max turns
    sys_msgs = [m for m in messages if m["role"] == "system"]
    non_sys = [m for m in messages if m["role"] != "system"]
    if len(non_sys) > MAX_TURNS * 2:
        non_sys = non_sys[-(MAX_TURNS * 2):]
    messages = sys_msgs + non_sys

    # Agentic tool loop
    response_text = ""
    for _ in range(3):
        response_text = _call_model(messages)
        tool_name, tool_args = _parse_tool_call(response_text)
        if not tool_name:
            break
        tool_result = execute_tool(tool_name, tool_args or {})
        tools_used.append(tool_name)
        messages.append({"role": "assistant", "content": response_text})
        messages.append({"role": "user", "content": f"[Tool {tool_name} result]: {tool_result}"})

    # Output guardrail
    if not is_safe_output(response_text):
        response_text = "[Response filtered by safety system.]"

    latency_ms = (time.time() - start) * 1000
    log_request(user_message, response_text, latency_ms, tools_used)

    # Append latency footer
    footer = f"\n\n---\n*⏱ {latency_ms:.0f}ms*"
    if tools_used:
        footer += f" *| 🔧 {', '.join(tools_used)}*"

    history.append([user_message, response_text + footer])
    return "", history


# ── Gradio UI ─────────────────────────────────────────────────────────────────
with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="indigo", secondary_hue="purple"),
    title="Qwen2.5 Personal Assistant",
) as demo:
    gr.Markdown(
        """# 🤖 Qwen2.5-0.5B Personal Assistant
        **Open-source AI assistant** with multi-turn memory, tools, guardrails, and observability.
        Built for the AI Assistant Evaluation challenge."""
    )

    with gr.Tab("💬 Chat"):
        chatbot = gr.Chatbot(height=500, label="Conversation")
        with gr.Row():
            msg = gr.Textbox(
                placeholder="Ask me anything…",
                show_label=False,
                scale=8,
            )
            send_btn = gr.Button("Send", variant="primary", scale=1)
        clear_btn = gr.Button("🗑 Clear conversation")

        send_btn.click(chat, [msg, chatbot], [msg, chatbot])
        msg.submit(chat, [msg, chatbot], [msg, chatbot])
        clear_btn.click(lambda: ([], ""), outputs=[chatbot, msg])

    with gr.Tab("📊 Observability"):
        gr.Markdown("### Request Log (live session)")

        def get_log_df():
            import pandas as pd
            if not request_log:
                return pd.DataFrame(columns=["ts", "user", "response_length", "latency_ms", "tools"])
            return pd.DataFrame(request_log)

        refresh_btn = gr.Button("🔄 Refresh")
        log_table = gr.Dataframe(
            value=get_log_df,
            every=10,
            label="Recent requests",
        )
        refresh_btn.click(get_log_df, outputs=log_table)

    with gr.Tab("💰 Cost & Latency"):
        gr.Markdown(COST_TABLE)
        gr.Markdown("""
### Notes
- **HF Spaces free tier**: no GPU, inference via the serverless API — ~3-8s latency.
- **ZeroGPU**: Hugging Face's on-demand GPU allocation — ~0.8-2s, still free.
- **Modal / RunPod / Replicate**: paid serverless GPU options for production use.
- Token costs are estimated for the Qwen2.5-0.5B-Instruct model size.
- Claude Sonnet frontier model shown for reference comparison.
        """)

    with gr.Tab("ℹ️ About"):
        gr.Markdown("""
### Architecture
- **Model**: `Qwen/Qwen2.5-0.5B-Instruct` via HuggingFace Inference API
- **Memory**: Sliding-window conversation (15 turns)
- **Tools**: Calculator, Date/Time, Web Search (DuckDuckGo)
- **Guardrails**: Regex-based input & output safety filters
- **Observability**: In-session request log with latency & tool tracking

### Safety Layers
1. **Input guard**: Blocks known jailbreak patterns and harmful request templates
2. **Output guard**: Filters responses matching unsafe output patterns
3. **Model safety**: Qwen2.5 has built-in alignment training
        """)

demo.launch()
