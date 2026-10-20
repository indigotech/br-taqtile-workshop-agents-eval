from datetime import date, timedelta
from pathlib import Path

from pydantic import BaseModel, Field, TypeAdapter


class ExpectedTrip(BaseModel):
    destination: str | None
    start_date: date | None
    end_date: date | None
    guests: int | None
    budget_amount: float | None


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
    itinerary_brief: str | None = Field(
        description="The facts the orchestrator hands the output generator for this trip, so the generator can be tested alone"
    )


_CASES = TypeAdapter(list[EvalCase])


def load_dataset(path: Path, today: date) -> list[EvalCase]:
    """Read the JSON array of cases, resolving date placeholders against `today`.

    Dates are placeholders (`{next_saturday}`, `{next_saturday_br}`, ...) rather
    than literals because the weather forecast only covers the next ~16 days: a
    case with fixed dates would stop exercising the weather agent a few weeks
    after it was written."""
    text = path.read_text(encoding="utf-8")
    for name, value in date_placeholders(today).items():
        text = text.replace("{" + name + "}", value)
    return _CASES.validate_json(text)


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
