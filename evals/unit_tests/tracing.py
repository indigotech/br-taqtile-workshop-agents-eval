import uuid
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def unit_test_trace(name: str) -> Iterator[None]:
    """One Langfuse trace tagged `unit-test`, with its own prompt cache key
    like every other entry point."""
    # Imported here so the conftest can import this module before it knows
    # whether app/ can be built at all.
    from app.core.model_client import prompt_cache_session
    from app.core.observability import observe_turn

    session_id = f"unit-test-{uuid.uuid4().hex[:8]}"
    with (
        prompt_cache_session(session_id),
        observe_turn(
            session_id=session_id,
            user_id=None,
            user_message=name,
            tags=["unit-test"],
        ),
    ):
        yield
