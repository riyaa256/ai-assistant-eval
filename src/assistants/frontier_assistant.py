import json
import time

from groq import Groq

from src.assistants.base import BaseAssistant
from src.guardrails.input_guard import check_input
from src.guardrails.output_guard import check_output
from src.observability.logger import RequestLog, make_request_id, now_iso
from src.tools.tool_registry import OPENAI_FORMAT_TOOLS, execute_tool

FRONTIER_SYSTEM_PROMPT = (
    "You are a helpful, harmless, and honest AI personal assistant powered by Llama 3.3. "
    "You help users with questions, writing, analysis, coding, and more. "
    "Maintain conversation context and refer back to earlier messages when relevant. "
    "When uncertain, say so. Always be accurate, helpful, and safe. "
    "Use your available tools (calculator, get_datetime, web_search) whenever they would "
    "give a more accurate or current answer."
)

DEFAULT_MODEL = "llama-3.3-70b-versatile"
MAX_TOOL_STEPS = 5


class FrontierAssistant(BaseAssistant):
    def __init__(self, groq_api_key: str, model: str = DEFAULT_MODEL):
        super().__init__(
            model_name=model,
            model_type="frontier",
            system_prompt=FRONTIER_SYSTEM_PROMPT,
        )
        self._client = Groq(api_key=groq_api_key)
        self._model = model

    def _build_messages(self, user_message: str) -> list[dict]:
        msgs = [{"role": "system", "content": FRONTIER_SYSTEM_PROMPT}]
        for user_msg, asst_msg in self.memory.get_history_display():
            msgs.append({"role": "user", "content": user_msg})
            msgs.append({"role": "assistant", "content": asst_msg})
        msgs.append({"role": "user", "content": user_message})
        return msgs

    def chat(self, message: str) -> tuple[str, dict]:
        start_time = time.time()
        request_id = make_request_id()
        tool_calls_made: list[dict] = []

        # Input guardrail
        guard = check_input(message)
        if guard.blocked:
            response_text = "I'm sorry, I can't help with that request."
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

        try:
            messages = self._build_messages(message)
            in_tok = out_tok = 0
            response_text = ""

            for _ in range(MAX_TOOL_STEPS):
                resp = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    tools=OPENAI_FORMAT_TOOLS,
                    tool_choice="auto",
                )
                usage = resp.usage
                if usage:
                    in_tok += usage.prompt_tokens or 0
                    out_tok += usage.completion_tokens or 0

                choice = resp.choices[0]
                msg = choice.message

                if choice.finish_reason == "tool_calls" and msg.tool_calls:
                    # Append assistant's tool-call message
                    messages.append({
                        "role": "assistant",
                        "content": msg.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in msg.tool_calls
                        ],
                    })
                    # Execute each tool and append results
                    for tc in msg.tool_calls:
                        try:
                            args = json.loads(tc.function.arguments)
                        except Exception:
                            args = {}
                        result = execute_tool(tc.function.name, args)
                        tool_calls_made.append({"name": tc.function.name, "result": result})
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": str(result),
                        })
                else:
                    response_text = msg.content or ""
                    break

            # Output guardrail
            out_guard = check_output(response_text)
            final_response = out_guard.filtered_text

            self.memory.add_user_message(message)
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
                input_tokens=in_tok,
                output_tokens=out_tok,
                tool_calls=tool_calls_made,
                guardrail_triggered=not out_guard.safe,
                guardrail_category="output_filter" if not out_guard.safe else None,
            ))

            return final_response, {
                "latency_ms": latency_ms,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "tool_calls": tool_calls_made,
                "guardrail_blocked": False,
                "output_filtered": out_guard.filtered,
            }

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = f"Error: {e}"
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
