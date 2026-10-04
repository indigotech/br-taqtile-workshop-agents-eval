from app.core.agent import user_message
from app.core.messages import GenerationConfig
from tests.helpers import ScriptedModelClient, function_call_response, text_response


class TestEmbed:
    def test_one_vector_per_text_in_order(self) -> None:
        model_client = ScriptedModelClient(
            [], embeddings={"praia": [1.0, 0.0], "serra": [0.0, 1.0]}
        )

        vectors = model_client.embed(["serra", "praia"])

        assert vectors == [[0.0, 1.0], [1.0, 0.0]]
        assert model_client.embedded_texts == ["serra", "praia"]


class TestGenerate:
    def test_tool_calls_come_back_as_an_assistant_message(self) -> None:
        model_client = ScriptedModelClient(
            [function_call_response(("echo", {"message": "a"}))]
        )

        reply = model_client.generate(
            messages=[user_message("oi")], config=GenerationConfig()
        )

        assert reply.model_dump() == {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": reply.tool_calls[0].id,
                    "name": "echo",
                    "arguments": '{"message": "a"}',
                }
            ],
            "tool_call_id": None,
        }

    def test_completion_without_choices_still_yields_an_assistant_turn(self) -> None:
        empty_completion = text_response("ignorada").model_copy(update={"choices": []})
        model_client = ScriptedModelClient([empty_completion])

        reply = model_client.generate(
            messages=[user_message("oi")], config=GenerationConfig()
        )

        assert (reply.role, reply.content, reply.tool_calls) == ("assistant", None, [])
