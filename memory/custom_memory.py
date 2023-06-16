from typing import Any, Dict, List
from langchain.memory.chat_memory import BaseChatMemory
from langchain.schema import BaseMessage

def get_buffer_string(
    messages: List[BaseMessage], human_prefix: str = "Human", ai_prefix: str = "AI"
) -> str:
    """Get buffer string of messages."""
    string_messages = []
    for m in messages:
        string_messages.append(f"{m.content}")
    return "\n".join(string_messages)


class CustomBufferWindowMemory(BaseChatMemory):
    """Buffer for storing conversation memory."""

    ai_prefix: str = "AI"
    memory_key: str = "history"  #: :meta private:
    k: int = 5

    @property
    def buffer(self) -> List[BaseMessage]:
        """String buffer of memory."""
        return self.chat_memory.messages

    @property
    def memory_variables(self) -> List[str]:
        """Will always return list of memory variables.

        :meta private:
        """
        return [self.memory_key]

    def add_input_only(self, input_str: str) -> None:
        """Add only a user message to the chat memory."""
        self.chat_memory.add_user_message(input_str)

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        """Return history buffer."""

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        """Return history buffer."""

        buffer: Any = self.buffer[-self.k * 2 :] if self.k > 0 else []
        if not self.return_messages:
            buffer = get_buffer_string(
                buffer,
                human_prefix="",
                ai_prefix=self.ai_prefix,
            )
        return {self.memory_key: buffer}