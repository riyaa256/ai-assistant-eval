import json
import re
import time
from typing import Optional

from src.assistants.base import BaseAssistant
from src.guardrails.input_guard import check_input
from src.guardrails.output_guard import check_output
from src.observability.logger import RequestLog, make_request_id, now_iso
from src.tools.tool_registry import (
    OPENAI_FORMAT_TOOLS,
    TOOL_SYSTEM_ADDENDUM,
    execute_tool,
)

OSS_SYSTEM_PROMPT = (
    "You are a helpful, harmless, and honest AI personal assistant. "
    "You help users with questions, writing, analysis, coding, and more. "
    "You maintain conversation context and refer back to earlier parts of the conversation. "
    "When you don't know something, say so clearly. "
    "Never generate harmful, biased, or misleading content.\n"
    + TOOL_SYSTEM_ADDENDUM
)

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"


class OSSAssistant(BaseAssistant):
    def __init__(self, hf_token: str):
        super().__init__(
            model_name=MODEL_ID,
            model_type="oss",
            system_prompt=OSS_SYSTEM_PROMPT,
        )
        self.hf_token = hf_token
        self._client = None

    def _get_client(self):
        if self._client is None:
            from huggingface_hub import InferenceClient
            # provider="hf-inference" routes to the free HF Inference API
            # (api-inference.huggingface.co) — does not require Inference Providers permission
            self._client = InferenceClient(
                model=MODEL_ID,
                token=self.hf_token,
                provider="hf-inference",
            )
        return self._client

    def _call_model(self, messages: list[dict], max_tokens: int = 1024) -> tuple[str, int, int]:
        client = self._get_client()
        response = client.chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7,
        )
        content = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", max(1, len(str(messages)) // 4))
        output_tokens = getattr(usage, "completion_tokens", max(1, len(content) // 4))
        return content, input_tokens, output_tokens

    def _call_model_with_native_tools(
        self, messages: list[dict], max_tokens: int = 1024
    ) -> tuple[str, list[dict], int, int]:
        """Try native tool calling; fall back to prompt-based parsing."""
        client = self._get_client()
        try:
            response = client.chat_completion(
                messages=messages,
                tools=OPENAI_FORMAT_TOOLS,
                tool_choice="auto",
                max_tokens=max_tokens,
                temperature=0.7,
            )
            msg = response.choices[0].message
            tool_calls = getattr(msg, "tool_calls", None) or []
            usage = getattr(response, "usage", None)
            input_tokens = getattr(usage, "prompt_tokens", max(1, len(str(messages)) // 4))
            output_tokens = getattr(usage, "completion_tokens", 50)

            if tool_calls:
                parsed = []
                for tc in tool_calls:
                    fn = tc.function
                    args = json.loads(fn.arguments) if isinstance(fn.arguments, str) else fn.arguments
                    parsed.append({
                        "id": getattr(tc, "id", make_request_id()),
                        "name": fn.name,
                        "arguments": args,
                    })
                return msg.content or "", parsed, input_tokens, output_tokens

            content = msg.content or ""
            return content, [], input_tokens, output_tokens
        except Exception:
            # Fall back to plain call + regex parse
            content, in_tok, out_tok = self._call_model(messages, max_tokens)
            parsed = self._parse_tool_call_from_text(content)
            return content, parsed, in_tok, out_tok

    def _parse_tool_call_from_text(self, text: str) -> list[dict]:
        """Parse ```tool_call ... ``` blocks from model output."""
        pattern = r"```tool_call\s*\n(.*?)\n```"
        matches = re.findall(pattern, text, re.DOTALL)
        result = []
        for m in matches:
            try:
                data = json.loads(m.strip())
                result.append({
                    "id": make_request_id(),
                    "name": data.get("name", ""),
                    "arguments": data.get("arguments", {}),
                })
            except json.JSONDecodeError:
                pass
        return result

    def chat(self, message: str) -> tuple[str, dict]:
        start_time = time.time()
        request_id = make_request_id()
        tool_calls_made: list[dict] = []

        # Input guardrail
        guard = check_input(message)
        if guard.blocked:
            response_text = f"I'm sorry, I can't help with that. {guard.message}"
            latency_ms = (time.time() - start_time) * 1000
            self.logger.log_request(RequestLog(
                session_id=self._session_id,
                request_id=request_id,
                timestamp=now_iso(),
                model=self.model_name,
                model_type=self.model_type,
                user_message=message,
                assistant_response=response_text,
                latency_ms=latency_ms,
                input_tokens=0,
                output_tokens=0,
                guardrail_triggered=True,
                guardrail_category=guard.category,
            ))
            return response_text, {
                "latency_ms": latency_ms,
                "input_tokens": 0,
                "output_tokens": 0,
                "guardrail_blocked": True,
            }

        self.memory.add_user_message(message)
        messages = self.memory.get_messages_for_api()
        total_in = 0
        total_out = 0

        try:
            # Agentic tool loop (max 3 steps)
            for _step in range(3):
                content, parsed_tools, in_tok, out_tok = self._call_model_with_native_tools(messages)
                total_in += in_tok
                total_out += out_tok

                if not parsed_tools:
                    break

                # Add assistant's partial response
                messages.append({"role": "assistant", "content": content or ""})

                for tc in parsed_tools:
                    tool_result = execute_tool(tc["name"], tc["arguments"])
                    tool_calls_made.append({"name": tc["name"], "result": tool_result})
                    # Inject tool result for next model call
                    messages.append({
                        "role": "user",
                        "content": f"[Tool result for {tc['name']}]: {tool_result}",
                    })

            response_text = content

            # Output guardrail
            out_guard = check_output(response_text)
            final_response = out_guard.filtered_text

            self.memory.add_assistant_message(final_response)
            latency_ms = (time.time() - start_time) * 1000

            self.logger.log_request(RequestLog(
                session_id=self._session_id,
                request_id=request_id,
                timestamp=now_iso(),
                model=self.model_name,
                model_type=self.model_type,
                user_message=message,
                assistant_response=final_response,
                latency_ms=latency_ms,
                input_tokens=total_in,
                output_tokens=total_out,
                tool_calls=tool_calls_made,
                guardrail_triggered=not out_guard.safe,
                guardrail_category="output_filter" if not out_guard.safe else None,
            ))

            return final_response, {
                "latency_ms": latency_ms,
                "input_tokens": total_in,
                "output_tokens": total_out,
                "tool_calls": tool_calls_made,
                "guardrail_blocked": False,
                "output_filtered": out_guard.filtered,
            }

        except Exception as e:
            self.memory.remove_last_user_message()
            latency_ms = (time.time() - start_time) * 1000
            error_msg = f"Error communicating with model: {e}"
            self.logger.log_request(RequestLog(
                session_id=self._session_id,
                request_id=request_id,
                timestamp=now_iso(),
                model=self.model_name,
                model_type=self.model_type,
                user_message=message,
                assistant_response=error_msg,
                latency_ms=latency_ms,
                input_tokens=0,
                output_tokens=0,
                error=str(e),
            ))
            return error_msg, {"latency_ms": latency_ms, "error": str(e)}
