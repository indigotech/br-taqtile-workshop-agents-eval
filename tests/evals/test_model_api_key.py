import pytest

from evals.unit_tests.model_api_key import missing_model_api_key_reason


class TestMissingModelApiKeyReason:
    @pytest.mark.parametrize("model_api_key", [None, "", "   "])
    def test_missing_key_explains_how_to_configure_it(
        self, model_api_key: str | None
    ) -> None:
        reason = missing_model_api_key_reason(model_api_key)

        assert reason is not None
        assert "make setup-env" in reason

    @pytest.mark.parametrize("model_api_key", ["changethis", "test", " changethis "])
    def test_placeholder_key_is_not_a_real_one(self, model_api_key: str) -> None:
        reason = missing_model_api_key_reason(model_api_key)

        assert reason is not None
        assert model_api_key.strip() in reason

    def test_real_looking_key_runs_the_tests(self) -> None:
        assert missing_model_api_key_reason("sk-proj-abc123") is None
