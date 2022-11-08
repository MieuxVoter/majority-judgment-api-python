import typing as t
from datetime import datetime
from pydantic import BaseModel, Field, validator, ConstrainedSet, ConstrainedStr
from pydantic.fields import ModelField
from .settings import settings


def _empty_string():
    """
    Using the default factory for field
    """
    return ""


Name = t.Annotated[str, Field(min_length=1, max_length=255)]
Ref = t.Annotated[str, Field(default_factory=_empty_string, max_length=255)]
Image = t.Annotated[str, Field(default_factory=_empty_string, max_length=255)]
Description = t.Annotated[str, Field(default_factory=_empty_string, max_length=1024)]
GradeValue = t.Annotated[int, Field(ge=0, lt=settings.max_grades)]
Color = t.Annotated[str, Field(min_length=3, max_length=10)]


def _causal_dates_validator(*fields: str):
    """
    Create a validator to assess the temporal logic for a list of field
    """

    def _validator_fn(value: datetime, values: dict[str, datetime], field: ModelField):
        """
        Check that the field date_created happens before the field date_modified.
        """
        if field.name not in fields:
            return value

        if any(f not in values or values[f] is None for f in fields):
            return value

        idx_field = fields.index(field.name)
        for i, f in enumerate(fields):
            if i < idx_field and values[f] > value:
                raise ValueError(f"{f} is after {field.name}")
            if i > idx_field and values[f] < value:
                raise ValueError(f"{f} is before {field.name}")

        return value

    return validator(
        *fields,
        allow_reuse=True,
        always=True,
    )(_validator_fn)


class Candidate(BaseModel):
    name: Name
    description: Description
    image: Image
    date_created: datetime
    date_modified: datetime

    _valid_date = _causal_dates_validator("date_created", "date_modified")

    class Config:
        orm_mode = True


class Grade(BaseModel):
    name: Name
    value: GradeValue
    description: Description
    date_created: datetime
    date_modified: datetime

    _valid_date = _causal_dates_validator("date_created", "date_modified")

    class Config:
        orm_mode = True
        frozen = True  # to allow set


class Vote(BaseModel):
    candidate: Candidate
    grade: Grade
    date_created: datetime
    date_modified: datetime

    _valid_date = _causal_dates_validator("date_created", "date_modified")

    class Config:
        orm_mode = True


class SetGrades(ConstrainedSet):
    item_item = Grade
    min_items = 2
    max_items = settings.max_grades


class SetCandidates(ConstrainedSet):
    item_item = Candidate
    min_items = 2
    max_items = settings.max_candidates


class Election(BaseModel):
    name: Name
    description: Description
    ref: Ref
    grades: SetGrades
    candidates: SetCandidates
    date_created: datetime
    date_modified: datetime
    num_voters: int = Field(..., ge=0, le=settings.max_voters)
    date_start: datetime | None = None
    date_end: datetime | None = None
    hide_results: bool = True
    force_close: bool = False
    private: bool = False

    _valid_date = _causal_dates_validator("date_created", "date_modified")
    _valid_date = _causal_dates_validator("date_start", "date_end")

    @validator("hide_results", "num_voters", "date_end")
    def can_finish(cls, value: str, values: dict[str, t.Any], field: ModelField):
        """
        Enforce that the election is finish-able
        """
        if "hide_results" in values:
            hide_results = values["hide_results"]
        elif field.name == "hide_results":
            hide_results = value
        else:
            return value

        if "num_voters" in values:
            num_voters = values["num_voters"]
        elif field.name == "num_voters":
            num_voters = value
        else:
            return value

        if "date_end" in values:
            date_end = values["date_end"]
        elif field.name == "date_end":
            date_end = value
        else:
            return value

        if hide_results and num_voters == 0 and date_end is None:
            raise ValueError("This election can not end")

    class Config:
        orm_mode = True


class ElectionCreate(Election):
    pass
