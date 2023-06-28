from typing import Any, Dict, List
from langchain.memory.chat_memory import BaseChatMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage, ChatMessage

def get_buffer_string(
    messages: List[BaseMessage], human_prefix: str = "Human", ai_prefix: str = "AI"
) -> str:
    """Get buffer string of messages."""
    string_messages = []
    for m in messages:
        if isinstance(m, HumanMessage):
            role = human_prefix
        elif isinstance(m, AIMessage):
            role = ai_prefix
        elif isinstance(m, SystemMessage):
            role = "System"
        elif isinstance(m, ChatMessage):
            role = m.role
        else:
            raise ValueError(f"Got unsupported message type: {m}")
        if role == human_prefix:
            string_messages.append(f"{m.content}")
        else:
            string_messages.append(f"{role}: {m.content}")

    return "\n".join(string_messages)


class CustomBufferWindowMemory(BaseChatMemory):
    """Buffer for storing conversation memory."""

    ai_prefix: str = "AI"
    memory_key: str = "history"
    k: int = 5

    @property
    def buffer(self) -> List[BaseMessage]:
        """String buffer of memory."""
        return self.chat_memory.messages

    @property
    def memory_variables(self) -> List[str]:
        """Will always return list of memory variables."""
        return [self.memory_key]

    def add_input_only(self, input_str: str) -> None:
        """Add only a user message to the chat memory."""
        self.chat_memory.messages.append(HumanMessage(content=input_str))

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        """Return history buffer."""
        buffer: Any = self.buffer[-self.k * 2 :] if self.k > 0 else []
        buffer = get_buffer_string(
            buffer,
            human_prefix="",
            ai_prefix=self.ai_prefix,
        )
        return {self.memory_key: buffer}
