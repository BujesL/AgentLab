import json
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from engine.models import Dataset


@dataclass
class ValidationResult:
    ok: bool
    dataset: Dataset | None = None
    errors: list[str] = field(default_factory=list)


def load_dataset_raw(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_dataset(path: Path) -> ValidationResult:
    try:
        raw = load_dataset_raw(path)
    except (OSError, json.JSONDecodeError) as e:
        return ValidationResult(ok=False, errors=[f"could not read/parse {path}: {e}"])

    try:
        dataset = Dataset.model_validate(raw)
    except ValidationError as e:
        errors = [
            f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in e.errors()
        ]
        return ValidationResult(ok=False, errors=errors)

    return ValidationResult(ok=True, dataset=dataset)


def load_dataset(path: Path) -> Dataset:
    result = validate_dataset(path)
    if not result.ok or result.dataset is None:
        raise ValueError(f"invalid dataset at {path}: {result.errors}")
    return result.dataset
