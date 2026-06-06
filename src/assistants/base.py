from abc import ABC, abstractmethod
from src.memory.conversation_memory import ConversationMemory
from src.observability.logger import ObservabilityLogger


class BaseAssistant(ABC):
    def __init__(
        self,
        model_name: str,
        model_type: str,
        system_prompt: str,
        max_memory_turns: int = 20,
    ):
        self.model_name = model_name
        self.model_type = model_type
        self.memory = ConversationMemory(
            max_turns=max_memory_turns,
            system_prompt=system_prompt,
        )
        self.logger = ObservabilityLogger(model_type)
        self._session_id = "default"

    def set_session_id(self, session_id: str):
        self._session_id = session_id

    @abstractmethod
    def chat(self, message: str) -> tuple[str, dict]:
        """Send a message and return (response_text, metadata)."""
        pass

    def clear_history(self):
        self.memory.clear()

    def get_stats(self) -> dict:
        return self.logger.get_stats()

    def get_history(self) -> list[tuple[str, str]]:
        return self.memory.get_history_display()
