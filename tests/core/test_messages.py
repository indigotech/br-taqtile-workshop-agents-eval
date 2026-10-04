from app.core.messages import (
    ChatMessage,
    ToolCall,
    history_for_next_turn,
    text_exchanges,
)


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


class TestHistoryForNextTurn:
    def test_latest_turn_keeps_its_tool_traffic_and_earlier_turns_keep_text(
        self,
    ) -> None:
        earlier_tool_call = ToolCall(id="call_1", name="echo", arguments="{}")
        latest_tool_call = ToolCall(id="call_2", name="echo", arguments="{}")
        messages = [
            ChatMessage(role="user", content="Paraty?"),
            ChatMessage(role="assistant", tool_calls=[earlier_tool_call]),
            ChatMessage(role="tool", tool_call_id="call_1", content="{}"),
            ChatMessage(role="assistant", content="Casa Caiçara, R$ 260."),
            ChatMessage(role="user", content="Pode reservar"),
            ChatMessage(role="assistant", tool_calls=[latest_tool_call]),
            ChatMessage(role="tool", tool_call_id="call_2", content="{}"),
            ChatMessage(role="assistant", content="Reservado."),
        ]

        assert history_for_next_turn(messages) == [
            messages[0],
            ChatMessage(role="assistant", content="Casa Caiçara, R$ 260."),
            *messages[4:],
        ]
