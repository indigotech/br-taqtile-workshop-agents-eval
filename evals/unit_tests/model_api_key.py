# Placeholder keys that would only fail at the first model call: the one
# sample.env ships with and the fake one test.env sets for the offline suite.
_PLACEHOLDER_KEYS = frozenset({"changethis", "test"})


def missing_model_api_key_reason(model_api_key: str | None) -> str | None:
    """Why the real-model unit tests can't run with this key, or None when it
    looks like a real one."""
    key = (model_api_key or "").strip()
    if not key:
        return (
            "MODEL_API_KEY não configurada, e estes testes chamam o modelo de "
            "verdade. Rode `make setup-env` e preencha MODEL_API_KEY no .env."
        )
    if key in _PLACEHOLDER_KEYS:
        return (
            f"MODEL_API_KEY ainda é o valor de exemplo ('{key}'), e estes testes "
            "chamam o modelo de verdade. Preencha uma chave real no .env."
        )
    return None
