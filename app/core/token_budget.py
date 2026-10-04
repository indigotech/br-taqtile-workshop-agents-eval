import logging
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class TokenBudget(BaseModel):
    limit: int | None
    tokens_used: int = 0


class TokenBudgetExceededError(Exception):
    def __init__(self, limit: int, tokens_used: int) -> None:
        super().__init__(
            f"Token budget exceeded: {tokens_used} of {limit} tokens used in this turn"
        )
        self.limit = limit
        self.tokens_used = tokens_used


# A context variable rather than a parameter threaded through Agent, the tool
# loop and AgentTool: sub-agents run synchronously in the same context as the
# orchestrator, so every nested model call charges the same turn's budget.
_current_budget: ContextVar[TokenBudget | None] = ContextVar(
    "current_token_budget", default=None
)


@contextmanager
def turn_token_budget() -> Iterator[TokenBudget]:
    """Counts the input and output tokens of every model call made inside it,
    sub-agents included, against `settings.MODEL_TOKEN_BUDGET_PER_TURN`
    (0 disables the limit, the count still runs)."""
    budget = TokenBudget(limit=settings.MODEL_TOKEN_BUDGET_PER_TURN or None)
    context_token = _current_budget.set(budget)
    try:
        yield budget
    finally:
        _current_budget.reset(context_token)


def ensure_within_budget() -> None:
    """Refuse to start a model call once the turn has spent its budget.

    Checked before a call rather than after the one that crosses the limit: that
    call is already paid for, so its reply is still used — when it is the final
    answer, the turn ends normally instead of throwing it away."""
    budget = _current_budget.get()
    if budget is None or budget.limit is None:
        return
    if budget.tokens_used >= budget.limit:
        logger.warning(
            "Refusing a model call: %s of %s tokens already used in this turn",
            budget.tokens_used,
            budget.limit,
        )
        raise TokenBudgetExceededError(budget.limit, budget.tokens_used)


def charge_tokens(tokens: int) -> None:
    budget = _current_budget.get()
    if budget is not None:
        budget.tokens_used += tokens
