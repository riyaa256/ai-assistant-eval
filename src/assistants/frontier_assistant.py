import time

from google import genai
from google.genai import types

from src.assistants.base import BaseAssistant
from src.guardrails.input_guard import check_input
from src.guardrails.output_guard import check_output
from src.observability.logger import RequestLog, make_request_id, now_iso
from src.tools.tool_registry import execute_tool

FRONTIER_SYSTEM_PROMPT = (
    "You are a helpful, harmless, and honest AI personal assistant powered by Gemini. "
    "You help users with questions, writing, analysis, coding, and more. "
    "Maintain conversation context and refer back to earlier messages when relevant. "
    "When uncertain, say so. Always be accurate, helpful, and safe. "
    "Use your available tools (calculator, get_datetime, web_search) whenever they would "
    "give a more accurate or current answer."
)

DEFAULT_MODEL = "gemini-2.0-flash"


def _calculator(expression: str) -> str:
    """Evaluate a mathematical expression like 'sqrt(16) + 2*3'. Returns the result."""
    return execute_tool("calculator", {"expression": expression})


def _get_datetime(timezone: str = "UTC") -> str:
    """Get the current date and time. Optionally pass a timezone like 'America/New_York'."""
    return execute_tool("get_datetime", {"timezone": timezone})


def _web_search(query: str, max_results: int = 3) -> str:
    """Search the internet for current information about any topic."""
    return execute_tool("web_search", {"query": query, "max_results": max_results})


TOOL_FUNCTIONS = {
    "_calculator": "calculator",
    "_get_datetime": "get_datetime",
    "_web_search": "web_search",
}


class FrontierAssistant(BaseAssistant):
    def __init__(self, gemini_api_key: str, model: str = DEFAULT_MODEL):
        super().__init__(
            model_name=model,
            model_type="frontier",
            system_prompt=FRONTIER_SYSTEM_PROMPT,
        )
        self._client = genai.Client(api_key=gemini_api_key)
        self._model = model

    def _build_history(self) -> list:
        """Convert our memory to Gemini Content objects."""
        history = []
        for user_msg, assistant_msg in self.memory.get_history_display():
            history.append(types.Content(role="user", parts=[types.Part(text=user_msg)]))
            history.append(types.Content(role="model", parts=[types.Part(text=assistant_msg)]))
        return history

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
            config = types.GenerateContentConfig(
                system_instruction=FRONTIER_SYSTEM_PROMPT,
                tools=[_calculator, _get_datetime, _web_search],
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=False
                ),
            )

            history = self._build_history()
            history.append(types.Content(role="user", parts=[types.Part(text=message)]))

            response = self._client.models.generate_content(
                model=self._model,
                contents=history,
                config=config,
            )

            # Handle automatic function calling — SDK executes tools and returns final text
            response_text = response.text or ""

            # Check if any tool calls were recorded in the response
            for candidate in response.candidates or []:
                for part in candidate.content.parts or []:
                    if hasattr(part, "function_call") and part.function_call:
                        fc = part.function_call
                        tool_key = TOOL_FUNCTIONS.get(fc.name, fc.name.lstrip("_"))
                        tool_calls_made.append({
                            "name": tool_key,
                            "result": execute_tool(tool_key, dict(fc.args)),
                        })

            # Output guardrail
            out_guard = check_output(response_text)
            final_response = out_guard.filtered_text

            self.memory.add_user_message(message)
            self.memory.add_assistant_message(final_response)

            latency_ms = (time.time() - start_time) * 1000
            usage = getattr(response, "usage_metadata", None)
            in_tok = getattr(usage, "prompt_token_count", max(1, len(message) // 4)) or max(1, len(message) // 4)
            out_tok = getattr(usage, "candidates_token_count", max(1, len(final_response) // 4)) or max(1, len(final_response) // 4)

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
