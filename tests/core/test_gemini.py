from tests.helpers import ScriptedGeminiClient


class TestEmbed:
    def test_one_vector_per_text_in_order(self) -> None:
        gemini = ScriptedGeminiClient(
            [], embeddings={"praia": [1.0, 0.0], "serra": [0.0, 1.0]}
        )

        vectors = gemini.embed(["serra", "praia"])

        assert vectors == [[0.0, 1.0], [1.0, 0.0]]
        assert gemini.embedded_texts == ["serra", "praia"]
