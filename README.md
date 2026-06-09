# AI Assistant Evaluation Platform

A full-stack comparison platform for **OSS (Llama 3.1-8B)** vs **Frontier (Llama 3.3-70B)** AI personal assistants — with multi-turn memory, tool use, guardrails, observability, and an automated LLM-as-judge evaluation framework.

Both models are served via **Groq** (free, hardware-accelerated, no credit card required).

---

## Live Demo

| URL | Stack |
|---|---|
| `localhost:8502` | Streamlit — local development |
| HuggingFace Spaces | Gradio — public deployment (see `deployment/`) |

---

## Features

| Feature | OSS (Llama 3.1-8B) | Frontier (Llama 3.3-70B) |
|---|---|---|
| Multi-turn memory | Sliding window, 20 turns | Sliding window, 20 turns |
| Tool use | Native OpenAI-format, 3-step loop | Native OpenAI-format, 5-step loop |
| Calculator | AST-based safe eval | AST-based safe eval |
| Web search | DuckDuckGo | DuckDuckGo |
| Date / Time | zoneinfo-based | zoneinfo-based |
| Input guardrails | Regex blocklist | Regex blocklist |
| Output guardrails | Pattern filter | Pattern filter |
| Structured logging | JSONL per request | JSONL per request |
| Latency tracking | Per request (ms) | Per request (ms) |
| Token counting | Input + output | Input + output |

---

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Groq API key (free, no credit card) — sign up at [console.groq.com](https://console.groq.com), click **API Keys → Create API key**. Key starts with `gsk_...`

### 2. Install & Run

```bash
git clone https://github.com/riyaa256/ai-assistant-eval
cd ai-assistant-eval

pip install -r requirements.txt

cp .env.example .env
# Open .env and paste your GROQ_API_KEY
```

`.env` file:
```
GROQ_API_KEY=gsk_your_key_here
```

```bash
streamlit run app.py
```

Opens at `http://localhost:8502`. The API key is loaded automatically from `.env` — it is never shown in the UI.

### 3. Navigation

The app uses a custom left-panel navigation (no Streamlit sidebar). Click any nav link to switch pages:

| Page | What it does |
|---|---|
| OSS Assistant | Chat with Llama 3.1-8B — the small, fast open-source model |
| Frontier Assistant | Chat with Llama 3.3-70B — the large frontier-class model |
| Side-by-Side | Send one prompt to both models, compare responses and latency |
| Evaluate | Run the full 30-prompt evaluation suite with LLM-as-judge scoring |

---

## Architecture

### OSS Assistant (`src/assistants/oss_assistant.py`)

```
User message
  → Input guardrail (regex blocklist: jailbreak, violence, CSAM, self-harm)
  → Conversation memory (sliding window, last 20 turns)
  → Groq API: llama-3.1-8b-instant
  → Tool loop (up to 3 steps, native OpenAI-format function calling)
      → calculator | get_datetime | web_search
  → Output guardrail (regex pattern filter)
  → JSONL log (logs/oss_logs.jsonl)
  → Response
```

### Frontier Assistant (`src/assistants/frontier_assistant.py`)

```
User message
  → Input guardrail
  → Conversation memory
  → Groq API: llama-3.3-70b-versatile
  → Tool loop (up to 5 steps, native OpenAI-format function calling)
  → Output guardrail
  → JSONL log (logs/frontier_logs.jsonl)
  → Response
```

Both assistants use the same Groq SDK and OpenAI-compatible tool-calling format. The difference is model size (8B vs 70B), tool loop depth (3 vs 5 steps), and context capacity.

### Memory (`src/memory/conversation_memory.py`)

Sliding-window: keeps the last 20 user/assistant turns. Deterministic, no extra API calls, avoids context-length issues. System prompt is prepended on every call.

### Guardrails (`src/guardrails/`)

Two layers:
1. **Input guard** — Regex patterns covering jailbreak attempts, violence, illegal drugs, CSAM, self-harm. Blocks before the model is called, zero latency.
2. **Output guard** — Pattern match on the generated response. Replaces harmful output with a safety message.

### Observability (`src/observability/logger.py`)

Every request is logged as a JSONL entry:
```json
{
  "session_id": "a3f91c",
  "request_id": "b2e04d",
  "timestamp": "2026-06-12T15:00:00Z",
  "model": "llama-3.1-8b-instant",
  "latency_ms": 385,
  "input_tokens": 449,
  "output_tokens": 53,
  "tool_calls": [],
  "guardrail_triggered": false
}
```

---

## Evaluation Framework

### Test Suite (`src/evaluation/prompts.py`)

30 structured prompts across 3 categories:

| Category | Count | Measures |
|---|---|---|
| Factual | 10 | Accuracy, hallucination rate |
| Adversarial / Jailbreak | 10 | Safety score, jailbreak resistance |
| Bias / Sensitive | 10 | Neutrality, fairness, stereotyping |

### LLM-as-Judge (`src/evaluation/judge.py`)

Uses **Llama 3.3-70B via Groq** to score each response with category-specific rubrics:

- **Factual**: `accuracy_score` (0-10), `hallucination_detected`, `contains_correct_answer`
- **Adversarial**: `safety_score` (0-10), `jailbreak_success`, `refusal_quality` (0-10)
- **Bias**: `neutrality_score` (0-10), `bias_detected`, `stereotype_reinforced`

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

## UI Design

The frontend is a custom Streamlit layout — no Streamlit sidebar. Navigation is a pure HTML left panel with `?page=` query params so the URL reflects the current view. All emojis removed.

**Color palette**: deep purple nav (`#38265a`) on a soft lavender background (`#bfadd6`), white content cards, Inter font throughout.

---

## HuggingFace Spaces Deployment

The `deployment/hf_spaces/` directory contains a standalone Gradio app.

1. Create a Space at [huggingface.co/new-space](https://huggingface.co/new-space) — SDK: **Gradio**, Hardware: **CPU free**
2. Upload `deployment/hf_spaces/app.py` and `deployment/hf_spaces/requirements.txt`
3. Add `GROQ_API_KEY` as a **Secret** in Space Settings

### Cost & Latency Table

| Platform | Avg Latency | Cost / 1k tokens | Notes |
|---|---|---|---|
| Groq (8B) — OSS | 200–500 ms | Free tier | 14,400 req/day, LPU hardware |
| Groq (70B) — Frontier | 300–800 ms | Free tier / ~$0.0006 | Same free tier |
| HF Spaces CPU | 3–8 s | $0.00 | Shared, rate-limited |
| HF Spaces ZeroGPU | 0.8–2 s | ~$0.001 | A100, free tier |
| Modal (A10G) | 0.4–1.2 s | ~$0.002 | Cold-start ~2 s |
| RunPod (RTX 4090) | 0.3–0.9 s | ~$0.003 | Persistent endpoint |

---

## Architecture Decisions

### Why Llama models on Groq?

Groq's LPU hardware delivers sub-second inference on 70B models — faster than most GPU cloud providers. Both models are completely free (14,400 req/day). Using the same provider for both OSS and Frontier means latency differences reflect model size, not infrastructure.

### Why 8B vs 70B for the comparison?

Llama 3.1-8B is a realistic "small OSS" deployment (runs on a single consumer GPU). Llama 3.3-70B is a frontier-class model matching GPT-4o on many benchmarks. The gap between them illustrates what larger scale buys.

### Why sliding-window memory?

Deterministic and cheap — no extra API calls, no vector DB. For a 20-turn window the context is always bounded. For the 8B model this is especially important as long contexts degrade quality.

### Why regex guardrails?

Sub-millisecond latency, no API dependency, zero cost. A model-based classifier (Llama Guard) would catch subtler attacks but adds ~500ms and an extra API call. The layered approach (fast regex → model alignment → output check) covers the main failure modes.

### Why DuckDuckGo for web search?

Free, no API key, good enough for demos. Serper/Bing/Google would be more reliable in production.

---

## Tradeoffs

| Decision | Chosen | Alternative | Reason |
|---|---|---|---|
| Inference provider | Groq (free) | Together AI, Replicate | Fastest free option, no card |
| OSS model | llama-3.1-8b-instant | Mistral 7B, Gemma 9B | Best quality at 8B on Groq |
| Frontier model | llama-3.3-70b-versatile | GPT-4o, Claude 3.5 | Free vs paid |
| Memory | Sliding window | Vector DB (RAG) | Simplicity vs semantic retrieval |
| Guardrails | Regex | Llama Guard | Zero latency vs better coverage |
| UI framework | Streamlit | FastAPI + React | Speed-to-demo vs customisability |

---

## What I Would Improve With More Time

1. **Streaming responses** — SSE streaming for real-time token-by-token display
2. **Semantic long-term memory** — Store conversation summaries in ChromaDB / Pinecone for cross-session retrieval
3. **Model-based safety layer** — Integrate Llama Guard as a second guardrail tier
4. **Larger eval set** — 100+ prompts with verified ground truth, bootstrap confidence intervals
5. **Persistent sessions** — SQLite backend so conversation history survives restarts
6. **Caching** — LRU cache for repeated queries to reduce latency during evaluation
7. **A/B testing stats** — Statistical significance tests on OSS vs Frontier metric differences
8. **Larger OSS model** — Llama 3.1-70B as "OSS frontier" for a fairer apples-to-apples quality comparison

---

## Project Structure

```
ai-assistant-eval/
├── app.py                         # Streamlit app — custom nav, 4 pages
├── requirements.txt               # groq, streamlit, plotly, pandas, duckduckgo_search
├── .env.example                   # GROQ_API_KEY template
├── logs/                          # JSONL request logs (auto-created)
├── src/
│   ├── assistants/
│   │   ├── base.py                # Abstract BaseAssistant
│   │   ├── oss_assistant.py       # Llama 3.1-8B via Groq
│   │   └── frontier_assistant.py  # Llama 3.3-70B via Groq
│   ├── memory/
│   │   └── conversation_memory.py # Sliding-window history
│   ├── tools/
│   │   ├── tool_registry.py       # OpenAI-format tool definitions
│   │   ├── calculator.py          # Safe AST-based calculator
│   │   ├── datetime_tool.py       # Current date/time (zoneinfo)
│   │   └── web_search.py          # DuckDuckGo search
│   ├── guardrails/
│   │   ├── input_guard.py         # Input safety (regex blocklist)
│   │   └── output_guard.py        # Output safety (regex filter)
│   ├── observability/
│   │   └── logger.py              # Structured JSONL logging + session stats
│   └── evaluation/
│       ├── prompts.py             # 30 test prompts (factual / adversarial / bias)
│       ├── judge.py               # LLM-as-judge (Llama 3.3-70B via Groq)
│       └── eval_suite.py          # Evaluation runner + metrics aggregation
└── deployment/
    └── hf_spaces/
        ├── app.py                 # Standalone Gradio app for HF Spaces
        └── requirements.txt
```
