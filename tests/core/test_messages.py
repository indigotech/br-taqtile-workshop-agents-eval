from app.core.messages import ChatMessage, ToolCall, text_exchanges


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


class TestTextExchanges:
    def test_tool_calls_and_results_are_dropped_keeping_the_dialogue(self) -> None:
        messages = [
            ChatMessage(role="user", content="Paraty?"),
            ChatMessage(
                role="assistant",
                content="Vou ver.",
                tool_calls=[ToolCall(id="call_1", name="echo", arguments="{}")],
            ),
            ChatMessage(role="tool", tool_call_id="call_1", content='{"output": 1}'),
            ChatMessage(
                role="assistant",
                tool_calls=[ToolCall(id="call_2", name="echo", arguments="{}")],
            ),
            ChatMessage(role="tool", tool_call_id="call_2", content='{"output": 2}'),
            ChatMessage(role="assistant", content="Achei a Casa Caiçara."),
        ]

        assert [
            message.model_dump(exclude_none=True)
            for message in text_exchanges(messages)
        ] == [
            {"role": "user", "content": "Paraty?", "tool_calls": []},
            {"role": "assistant", "content": "Vou ver.", "tool_calls": []},
            {"role": "assistant", "content": "Achei a Casa Caiçara.", "tool_calls": []},
        ]
