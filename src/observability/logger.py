import json
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional


LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


@dataclass
class RequestLog:
    session_id: str
    request_id: str
    timestamp: str
    model: str
    model_type: str
    user_message: str
    assistant_response: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    tool_calls: list = field(default_factory=list)
    guardrail_triggered: bool = False
    guardrail_category: Optional[str] = None
    error: Optional[str] = None


class ObservabilityLogger:
    def __init__(self, model_type: str, log_file: Optional[str] = None):
        self.model_type = model_type
        self.log_file = Path(log_file) if log_file else LOGS_DIR / f"{model_type}_logs.jsonl"
        self._stats = {
            "total_requests": 0,
            "total_latency_ms": 0.0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "errors": 0,
            "guardrail_triggers": 0,
            "tool_calls": 0,
        }

    def log_request(self, log: RequestLog):
        with open(self.log_file, "a") as f:
            f.write(json.dumps(asdict(log)) + "\n")
        self._stats["total_requests"] += 1
        self._stats["total_latency_ms"] += log.latency_ms
        self._stats["total_input_tokens"] += log.input_tokens
        self._stats["total_output_tokens"] += log.output_tokens
        self._stats["tool_calls"] += len(log.tool_calls)
        if log.error:
            self._stats["errors"] += 1
        if log.guardrail_triggered:
            self._stats["guardrail_triggers"] += 1

    def get_stats(self) -> dict:
        s = self._stats.copy()
        n = s["total_requests"]
        s["avg_latency_ms"] = s["total_latency_ms"] / n if n else 0.0
        s["avg_input_tokens"] = s["total_input_tokens"] / n if n else 0.0
        s["avg_output_tokens"] = s["total_output_tokens"] / n if n else 0.0
        return s

    def get_all_logs(self) -> list[dict]:
        if not self.log_file.exists():
            return []
        logs = []
        with open(self.log_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return logs


def make_request_id() -> str:
    return str(uuid.uuid4())[:8]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
