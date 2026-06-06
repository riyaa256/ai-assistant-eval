import time

import anthropic

from src.assistants.base import BaseAssistant
from src.guardrails.input_guard import check_input
from src.guardrails.output_guard import check_output
from src.observability.logger import RequestLog, make_request_id, now_iso
from src.tools.tool_registry import ANTHROPIC_TOOLS, execute_tool

FRONTIER_SYSTEM_PROMPT = (
    "You are a helpful, harmless, and honest AI personal assistant powered by Claude. "
    "You help users with questions, writing, analysis, coding, and more. "
    "Maintain conversation context and refer back to earlier messages when relevant. "
    "When uncertain, say so. Always be accurate, helpful, and safe. "
    "Use your available tools (calculator, get_datetime, web_search) whenever they would "
    "give a more accurate or current answer."
)

DEFAULT_MODEL = "claude-sonnet-4-6"


class FrontierAssistant(BaseAssistant):
    def __init__(self, anthropic_api_key: str, model: str = DEFAULT_MODEL):
        super().__init__(
            model_name=model,
            model_type="frontier",
            system_prompt=FRONTIER_SYSTEM_PROMPT,
        )
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)

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

        self.memory.add_user_message(message)
        # Build message list without system (passed separately to Anthropic)
        api_messages = self.memory.get_messages_for_api(include_system=False)

        total_in = 0
        total_out = 0

        try:
            # Agentic tool loop
            while True:
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=1024,
                    system=self.memory.system_prompt,
                    messages=api_messages,
                    tools=ANTHROPIC_TOOLS,
                )

                total_in += response.usage.input_tokens
                total_out += response.usage.output_tokens

                if response.stop_reason == "tool_use":
                    tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

                    # Append assistant message with tool_use content blocks
                    api_messages.append({"role": "assistant", "content": response.content})

                    tool_results = []
                    for tu in tool_use_blocks:
                        result = execute_tool(tu.name, tu.input)
                        tool_calls_made.append({
                            "name": tu.name,
                            "input": tu.input,
                            "result": result,
                        })
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tu.id,
                            "content": result,
                        })

                    api_messages.append({"role": "user", "content": tool_results})
                    # Loop to get the final text response

                else:
                    # end_turn or other stop reason — extract text
                    response_text = "".join(
                        b.text for b in response.content if hasattr(b, "text")
                    )
                    break

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
