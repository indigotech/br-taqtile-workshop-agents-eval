import json
from datetime import date, timedelta
from pathlib import Path

from pydantic import BaseModel, Field


class ExpectedTrip(BaseModel):
    destination: str | None
    start_date: date | None
    end_date: date | None
    guests: int | None


class EvalCase(BaseModel):
    id: str
    description: str
    user_id: int
    messages: list[str] = Field(min_length=1)
    expected_trip: ExpectedTrip
    required_agents: list[str] = Field(
        description="Orchestrator tools that must be called while answering the first message"
    )
    user_preferences: list[str] = Field(
        description="What a good answer must take into account for this user"
    )
    confirmation_message_index: int | None = Field(
        description="Index of the message where the user confirms the booking; None means no booking may happen"
    )
    max_lodging_total: float | None = Field(
        description="Lodging total above which a booking breaks the user's budget"
    )
    reference_answer: str | None = Field(
        description="A good final answer, for similarity-based comparison"
    )


def load_dataset(path: Path, today: date) -> list[EvalCase]:
    """Read the JSONL dataset, resolving date placeholders against `today`.

    Dates are placeholders (`{next_saturday}`, `{next_saturday_br}`, ...) rather
    than literals because the weather forecast only covers the next ~16 days: a
    case with fixed dates would stop exercising the weather agent a few weeks
    after it was written."""
    placeholders = date_placeholders(today)
    cases: list[EvalCase] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        for name, value in placeholders.items():
            line = line.replace("{" + name + "}", value)
        cases.append(EvalCase.model_validate(json.loads(line)))
    return cases


def date_placeholders(today: date) -> dict[str, str]:
    days_until_saturday = (5 - today.weekday()) % 7 or 7
    next_saturday = today + timedelta(days=days_until_saturday)
    dates = {
        "today": today,
        "next_saturday": next_saturday,
        "next_sunday": next_saturday + timedelta(days=1),
        "saturday_in_5_weeks": next_saturday + timedelta(weeks=5),
        "sunday_in_5_weeks": next_saturday + timedelta(weeks=5, days=1),
    }
    placeholders: dict[str, str] = {}
    for name, value in dates.items():
        placeholders[name] = value.isoformat()
        placeholders[f"{name}_br"] = value.strftime("%d/%m")
    return placeholders
