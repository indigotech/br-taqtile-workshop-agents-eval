from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ToolCall(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    # Kept as the raw JSON string the model wrote: the history has to replay it
    # byte for byte, and parsing belongs to the ToolRegistry.
    arguments: str


class ChatMessage(BaseModel):
    """One turn of a conversation in the Chat Completions shape. The system
    prompt is not part of it: each agent sends its own on every request."""

    model_config = ConfigDict(frozen=True)

    role: Literal["user", "assistant", "tool"]
    content: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_call_id: str | None = None

    def as_param(self) -> dict[str, Any]:
        param: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.tool_calls:
            param["tool_calls"] = [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.name,
                        "arguments": tool_call.arguments,
                    },
                }
                for tool_call in self.tool_calls
            ]
        if self.tool_call_id is not None:
            param["tool_call_id"] = self.tool_call_id
        return param


class FunctionDeclaration(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    parameters: dict[str, Any]

    def as_param(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class GenerationConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    system_prompt: str | None = None
    temperature: float | None = None
    tools: list[FunctionDeclaration] = Field(default_factory=list)
    response_json_schema: dict[str, Any] | None = None
    prompt_cache_key: str | None = None


def text_exchanges(messages: list[ChatMessage]) -> list[ChatMessage]:
    """The user and assistant text of a conversation, without tool calls and
    tool results.

    Carried from one user turn to the next instead of the full history: every
    model call resends the history, and the tool traffic of earlier turns is
    most of it while the replies already summarize what it found."""
    return [
        ChatMessage(role=message.role, content=message.content)
        for message in messages
        if message.role in ("user", "assistant") and message.content
    ]
