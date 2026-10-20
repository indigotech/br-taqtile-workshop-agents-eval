from datetime import date
from pathlib import Path

from app.evals.dataset import EvalCase, load_dataset

DATASET_PATH = Path(__file__).parent / "dataset.json"


def golden_cases() -> list[EvalCase]:
    """Every case of evals/dataset.json, with its dates resolved against today."""
    return load_dataset(DATASET_PATH, date.today())


def golden_case(case_id: str) -> EvalCase:
    for case in golden_cases():
        if case.id == case_id:
            return case
    raise ValueError(f"No case {case_id!r} in {DATASET_PATH}")
