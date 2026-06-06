from dataclasses import dataclass
from typing import Optional


@dataclass
class Message:
    role: str
    content: str


class ConversationMemory:
    def __init__(self, max_turns: int = 20, system_prompt: str = ""):
        self.max_turns = max_turns
        self.system_prompt = system_prompt
        self._messages: list[Message] = []

    def add_user_message(self, content: str):
        self._messages.append(Message(role="user", content=content))
        self._trim()

    def add_assistant_message(self, content: str):
        self._messages.append(Message(role="assistant", content=content))

    def _trim(self):
        # Keep only the most recent max_turns pairs
        while len(self._messages) > self.max_turns * 2:
            self._messages.pop(0)

    def get_messages_for_api(self, include_system: bool = True) -> list[dict]:
        result = []
        if include_system and self.system_prompt:
            result.append({"role": "system", "content": self.system_prompt})
        for msg in self._messages:
            result.append({"role": msg.role, "content": msg.content})
        return result

    def clear(self):
        self._messages = []

    @property
    def message_count(self) -> int:
        return len(self._messages)

    @property
    def turn_count(self) -> int:
        return len([m for m in self._messages if m.role == "user"])

    def get_history_display(self) -> list[tuple[str, str]]:
        """Returns list of (user_msg, assistant_msg) tuples for display."""
        result = []
        user_msg: Optional[str] = None
        for msg in self._messages:
            if msg.role == "user":
                user_msg = msg.content
            elif msg.role == "assistant" and user_msg is not None:
                result.append((user_msg, msg.content))
                user_msg = None
        return result

    def remove_last_user_message(self):
        """Roll back the last user message (on error)."""
        for i in range(len(self._messages) - 1, -1, -1):
            if self._messages[i].role == "user":
                self._messages.pop(i)
                break
