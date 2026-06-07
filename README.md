# AI Assistant Evaluation Platform

A complete comparison platform for **Open-Source (Qwen2.5-0.5B-Instruct)** vs **Frontier (Llama 3.3-70B via Groq)** AI personal assistants — with multi-turn memory, tool use, guardrails, observability, and an automated LLM-as-judge evaluation framework.

---

## Features

| Feature | OSS (Qwen2.5) | Frontier (Llama 3.3) |
|---|---|---|
| Multi-turn memory | ✅ sliding window | ✅ sliding window |
| Tool use | ✅ prompt-based + native | ✅ native OpenAI-format tool calling |
| Calculator | ✅ | ✅ |
| Web search | ✅ DuckDuckGo | ✅ DuckDuckGo |
| Date/Time | ✅ | ✅ |
| Input guardrails | ✅ regex blocklist | ✅ regex blocklist |
| Output guardrails | ✅ pattern filter | ✅ pattern filter |
| Structured logging | ✅ JSONL | ✅ JSONL |
| Latency tracking | ✅ | ✅ |
| Token counting | ✅ | ✅ |
| HF Spaces deployment | ✅ Gradio app | — |

---

## Quick Start

### Prerequisites

- Python 3.10+
- HuggingFace token (free, read permissions) → [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
- Groq API key (free, no credit card) → [console.groq.com](https://console.groq.com) — click **"API Keys" → "Create API key"**, key starts with `gsk_...`

### Install & Run

```bash
git clone https://github.com/riyaa256/ai-assistant-eval
cd ai-assistant-eval

pip install -r requirements.txt

cp .env.example .env
# Edit .env — add your HF_TOKEN and GROQ_API_KEY

streamlit run app.py
```

The Streamlit app opens at `http://localhost:8501`. API keys are loaded automatically from `.env` — no need to type them in the UI.

### Tabs

| Tab | Description |
|---|---|
| 🔵 OSS Assistant | Chat with Qwen2.5-0.5B-Instruct (via HuggingFace Inference API) |
| 🟣 Frontier Assistant | Chat with Llama 3.3-70B (via Groq API) |
| ⚡ Side-by-Side | Send one prompt to both, compare responses instantly |
| 📊 Evaluate | Run 30-prompt evaluation suite with LLM-as-judge |

---

## Architecture

### OSS Assistant (`src/assistants/oss_assistant.py`)

```
User message
    → Input guardrail (regex blocklist)
    → Conversation memory (sliding window, 20 turns)
    → HF Inference API (Qwen2.5-0.5B-Instruct)
    → Tool call loop (up to 3 steps)
        → calculator / get_datetime / web_search
    → Output guardrail (pattern filter)
    → Structured log (logs/oss_logs.jsonl)
    → Response
```

**Tool calling strategy**: Tries native OpenAI-format tool calling via the HF API first; falls back to parsing ` ```tool_call``` ` JSON blocks from the model's text output. This dual strategy ensures reliability even when the small model doesn't emit well-formed tool call structures.

### Frontier Assistant (`src/assistants/frontier_assistant.py`)

```
User message
    → Input guardrail
    → Conversation memory
    → Groq API (llama-3.3-70b-versatile) with OpenAI-format tool calling
    → Tool execution loop (up to 5 steps, native function calling)
    → Output guardrail
    → Structured log (logs/frontier_logs.jsonl)
    → Response
```

Uses the `groq` Python SDK with the OpenAI-compatible chat completions API. Supports native function/tool calling — Groq returns `finish_reason="tool_calls"` and the code dispatches tools, appending results as `role="tool"` messages before the next completion call.

### Memory (`src/memory/conversation_memory.py`)

Sliding-window approach: keeps the last N user/assistant turns (default 20). Deterministic and avoids context-length issues on the 0.5B model. System prompt is prepended on every call.

### Guardrails (`src/guardrails/`)

Two layers:
1. **Input guard** (`input_guard.py`): Regex patterns covering jailbreak attempts, violence, illegal drugs, CSAM, self-harm. Blocks before the model is called.
2. **Output guard** (`output_guard.py`): Pattern match on the generated response. Replaces harmful output with a safety message.

### Observability (`src/observability/logger.py`)

Every request logs to a JSONL file:
```json
{
  "session_id": "abc12345",
  "request_id": "f3e21a",
  "timestamp": "2026-06-12T10:00:00Z",
  "model": "llama-3.3-70b-versatile",
  "latency_ms": 420,
  "input_tokens": 312,
  "output_tokens": 87,
  "tool_calls": [{"name": "calculator", "result": "2+2 = 4"}],
  "guardrail_triggered": false
}
```

---

## Evaluation Framework

### Test Suite (`src/evaluation/prompts.py`)

30 structured prompts in 3 categories:

| Category | Count | Tests For |
|---|---|---|
| Factual | 10 | Accuracy, hallucination rate |
| Adversarial/Jailbreak | 10 | Safety, jailbreak resistance |
| Bias/Sensitive | 10 | Fairness, neutrality, stereotyping |

### LLM-as-Judge (`src/evaluation/judge.py`)

Uses **Llama 3.3-70B (Groq)** to evaluate each response with category-specific rubrics:

- **Factual**: `accuracy_score` (0-10), `hallucination_detected` (bool), `contains_correct_answer`
- **Adversarial**: `safety_score` (0-10), `jailbreak_success` (bool), `refusal_quality` (0-10)
- **Bias**: `neutrality_score` (0-10), `bias_detected` (bool), `stereotype_reinforced` (bool)

### Metrics

| Metric | Formula |
|---|---|
| Hallucination Rate | `hallucinations / factual_prompts` |
| Avg Accuracy | mean `accuracy_score` across factual prompts |
| Jailbreak Rate | `jailbreaks / adversarial_prompts` |
| Avg Safety Score | mean `safety_score` across adversarial prompts |
| Bias Rate | `bias_detections / bias_prompts` |
| Avg Neutrality | mean `neutrality_score` across bias prompts |

---

## HuggingFace Spaces Deployment (Bonus)

The `deployment/hf_spaces/` directory contains a standalone Gradio app.

### Deploy to HF Spaces

1. Create a new Space: [huggingface.co/new-space](https://huggingface.co/new-space)
   - SDK: **Gradio**, Hardware: **CPU free** (or ZeroGPU for faster inference)
2. Upload `deployment/hf_spaces/app.py` as `app.py`
3. Upload `deployment/hf_spaces/requirements.txt` as `requirements.txt`
4. Add `HF_TOKEN` as a **Secret** in Space settings

### Cost & Latency Table

| Platform | Avg Latency | Cost / 1k tokens | Notes |
|---|---|---|---|
| HF Spaces CPU (free) | 3–8s | $0.00 | Shared, rate-limited |
| HF Spaces ZeroGPU | 0.8–2s | ~$0.001 | A100 on-demand, free tier |
| Modal (A10G serverless) | 0.4–1.2s | ~$0.002 | Cold-start ~2s |
| RunPod (RTX 4090) | 0.3–0.9s | ~$0.003 | Persistent endpoint |
| Replicate | 1–3s | ~$0.002 | Push-to-deploy |
| **Groq (Frontier)** | 0.2–0.8s | Free tier / ~$0.0006 | Hardware-accelerated LPU, 14k req/day free |

---

## Architecture Decisions

### Why Qwen2.5-0.5B-Instruct?
Recommended by the assignment for HF Spaces deployment. Small enough to run on free-tier serverless inference while still instruction-tuned. For production, Qwen2.5-7B or Llama 3.2-3B would give substantially better quality.

### Why Llama 3.3-70B via Groq as the Frontier model?
Completely free (14,400 requests/day, no credit card required), extremely fast (~200-800ms due to Groq's custom LPU hardware), and Llama 3.3-70B is a genuine frontier-class open model that matches GPT-4o on many benchmarks. Matches the assignment's intent for a "hosted foundation model" comparison.

### Why the `groq` SDK?
OpenAI-compatible API — the same tool-calling format used by the OSS model, making both assistants consistent. Groq's LPU hardware delivers sub-second latency even for the 70B model.

### Why sliding-window memory vs. summarization?
Sliding window is deterministic and doesn't require extra API calls. For the 0.5B OSS model, keeping context short (20 turns) also prevents quality degradation from long prompts.

### Why regex guardrails vs. model-based?
Regex runs in <1ms with no API dependency — ideal as a first-pass filter. A model-based classifier (e.g. Llama Guard) would catch subtler attacks but adds latency and cost. The layered approach (fast regex → model's own alignment → output check) covers the main failure modes.

### Why DuckDuckGo for web search?
Free, no API key required, sufficient for demo purposes. In production, Serper/Bing/Google would be more reliable.

---

## Tradeoffs

| Decision | Chosen | Alternative | Why |
|---|---|---|---|
| OSS model size | 0.5B | 7B+ | Free HF tier vs. better quality |
| Frontier model | Llama 3.3-70B (Groq) | GPT-4 / Claude | Free + fast vs. paid |
| Memory | Sliding window | Vector DB (RAG) | Simplicity vs. semantic retrieval |
| Guardrails | Regex | Llama Guard | Zero-latency vs. better coverage |
| Web search | DuckDuckGo | Serper/Google | Free vs. reliable |
| UI framework | Streamlit | FastAPI + React | Speed-to-demo vs. customisability |

---

## What I Would Improve With More Time

1. **Larger OSS model**: Qwen2.5-7B or Llama 3.2-3B for meaningfully better response quality and tool calling reliability.
2. **Semantic long-term memory**: Store conversation summaries in a vector DB (ChromaDB / Pinecone) for cross-session retrieval.
3. **Streaming responses**: SSE streaming for real-time token-by-token display in Streamlit.
4. **Model-based safety**: Integrate [Llama Guard](https://huggingface.co/meta-llama/LlamaGuard-7b) or [ShieldGemma](https://huggingface.co/google/shieldgemma-2b) as the second guardrail layer.
5. **Larger eval set**: 100+ prompts with verified ground truth, automated re-runs, statistical confidence intervals.
6. **Caching**: LRU cache for repeated queries to reduce latency and cost during evaluation.
7. **Persistent sessions**: SQLite/Postgres backend so conversation history survives restarts.
8. **A/B testing stats**: Bootstrap confidence intervals on metric differences to know if OSS vs. Frontier gaps are significant.

---

## Project Structure

```
ai-assistant-eval/
├── app.py                          # Main Streamlit app (4-tab UI)
├── requirements.txt
├── .env.example
├── logs/                           # JSONL request logs (auto-created)
├── src/
│   ├── assistants/
│   │   ├── base.py                 # Abstract BaseAssistant
│   │   ├── oss_assistant.py        # Qwen2.5 via HF Inference API
│   │   └── frontier_assistant.py   # Llama 3.3-70B via Groq API
│   ├── memory/
│   │   └── conversation_memory.py  # Sliding-window history
│   ├── tools/
│   │   ├── tool_registry.py        # Tool definitions (OpenAI + Anthropic format)
│   │   ├── calculator.py           # Safe AST-based calculator
│   │   ├── datetime_tool.py        # Current date/time
│   │   └── web_search.py           # DuckDuckGo search
│   ├── guardrails/
│   │   ├── input_guard.py          # Input safety (regex)
│   │   └── output_guard.py         # Output safety (regex)
│   ├── observability/
│   │   └── logger.py               # Structured JSONL logging + metrics
│   └── evaluation/
│       ├── prompts.py              # 30 test prompts (factual/adversarial/bias)
│       ├── judge.py                # LLM-as-judge (Llama 3.3-70B via Groq)
│       └── eval_suite.py           # Evaluation runner + metrics
└── deployment/
    └── hf_spaces/
        ├── app.py                  # Standalone Gradio app for HF Spaces
        └── requirements.txt
```
