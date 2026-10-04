from app.core.messages import ChatMessage, ToolCall


class TestAsParam:
    def test_assistant_tool_calls_are_sent_in_the_chat_completions_shape(
        self,
    ) -> None:
        message = ChatMessage(
            role="assistant",
            tool_calls=[
                ToolCall(id="call_1", name="echo", arguments='{"message": "a"}')
            ],
        )

        assert message.as_param() == {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "echo", "arguments": '{"message": "a"}'},
                }
            ],
        }

    def test_tool_result_carries_the_id_of_the_call_it_answers(self) -> None:
        message = ChatMessage(
            role="tool", tool_call_id="call_1", content='{"output": 1}'
        )

        assert message.as_param() == {
            "role": "tool",
            "content": '{"output": 1}',
            "tool_call_id": "call_1",
        }
