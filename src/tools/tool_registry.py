import json
from typing import Callable
from src.tools.calculator import run_calculator
from src.tools.datetime_tool import get_datetime
from src.tools.web_search import web_search


TOOL_FUNCTIONS: dict[str, Callable] = {
    "calculator": lambda args: run_calculator(args.get("expression", "")),
    "get_datetime": lambda args: get_datetime(args.get("timezone", "UTC")),
    "web_search": lambda args: web_search(args.get("query", ""), int(args.get("max_results", 3))),
}

# Anthropic native format
ANTHROPIC_TOOLS = [
    {
        "name": "calculator",
        "description": "Evaluate mathematical expressions. Supports arithmetic, powers, and functions like sqrt, sin, cos, log, floor, ceil.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The math expression, e.g. 'sqrt(144)', '(3+4)*2', 'log(100,10)'",
                }
            },
            "required": ["expression"],
        },
    },
    {
        "name": "get_datetime",
        "description": "Get the current date and time, optionally in a specific timezone.",
        "input_schema": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "IANA timezone, e.g. 'America/New_York', 'Europe/London'. Defaults to UTC.",
                }
            },
            "required": [],
        },
    },
    {
        "name": "web_search",
        "description": "Search the internet for current information on any topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
                "max_results": {
                    "type": "integer",
                    "description": "Number of results to return (1-5)",
                },
            },
            "required": ["query"],
        },
    },
]

# OpenAI-compatible format (for HF Inference API)
OPENAI_FORMAT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate mathematical expressions. Supports arithmetic, powers, sqrt, sin, cos, log.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "The math expression to evaluate"}
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_datetime",
            "description": "Get the current date and time in a specific timezone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {"type": "string", "description": "IANA timezone name, defaults to UTC"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the internet for current information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer"},
                },
                "required": ["query"],
            },
        },
    },
]

# Fallback system-prompt description for models that don't natively support tool use
TOOL_SYSTEM_ADDENDUM = """
## Tools Available

You may call tools by emitting a JSON block. Format:
```tool_call
{"name": "<tool>", "arguments": {<args>}}
```

Tools:
- **calculator**: `{"name": "calculator", "arguments": {"expression": "sqrt(16)+2"}}`
- **get_datetime**: `{"name": "get_datetime", "arguments": {"timezone": "UTC"}}`
- **web_search**: `{"name": "web_search", "arguments": {"query": "latest AI news"}}`

After a tool call I will show you the result; then give your final answer.
"""


def execute_tool(name: str, arguments: dict) -> str:
    if name not in TOOL_FUNCTIONS:
        return f"Error: unknown tool '{name}'"
    try:
        return str(TOOL_FUNCTIONS[name](arguments))
    except Exception as e:
        return f"Tool error: {e}"
