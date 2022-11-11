import typing as t
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator
from pydantic.fields import ModelField
from .settings import settings


def _empty_string():
    """
    Using the default factory for field
    """
    return ""


class ArgumentsSchemaError(Exception):
    """
    An error occured on the arguments provided to a schema
    """

Name = t.Annotated[str, Field(min_length=1, max_length=255)]
Ref = t.Annotated[str, Field(default_factory=_empty_string, max_length=255)]
Image = t.Annotated[str, Field(default_factory=_empty_string, max_length=255)]
Description = t.Annotated[str, Field(default_factory=_empty_string, max_length=1024)]
Color = t.Annotated[str, Field(min_length=3, max_length=10)]


def _causal_dates_validator(*fields: str):
    """
    Create a validator to assess the temporal logic for a list of field
    """

    def validator_fn(cls, value: datetime, values: dict[str, datetime], field):
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
                raise ArgumentsSchemaError(f"{f} is after {field.name}")
            if i > idx_field and values[f] < value:
                raise ArgumentsSchemaError(f"{f} is before {field.name}")

        return value

    return validator(
        *fields,
        allow_reuse=True,
        always=True,
    )(validator_fn)


class Candidate(BaseModel):
    name: Name
    description: Description
    image: Image
    date_created: datetime= Field(default_factory=datetime.now)
    date_modified: datetime= Field(default_factory=datetime.now)

    _valid_date = _causal_dates_validator("date_created", "date_modified")

    class Config:
        orm_mode = True


class CandidateRelational(Candidate):
    election_id: int

class Grade(BaseModel):
    name: Name
    value: int = Field(ge=0, lt=settings.max_grades, pre=True)
    description: Description
    date_created: datetime = Field(default_factory=datetime.now)
    date_modified: datetime = Field(default_factory=datetime.now)

    _valid_date = _causal_dates_validator("date_created", "date_modified")

    class Config:
        orm_mode = True


class GradeRelational(Grade):
    election_id: int

class Vote(BaseModel):
    candidate: Candidate
    grade: Grade
    date_created: datetime= Field(default_factory=datetime.now)
    date_modified: datetime= Field(default_factory=datetime.now)

    _valid_date = _causal_dates_validator("date_created", "date_modified")

    class Config:
        orm_mode = True



def _in_a_long_time() -> datetime:
    """
    Provides the date in the future
    """
    return datetime.now() + timedelta(weeks=10 * 52)

class Election(BaseModel):
    name: Name
    grades: list[Grade] = Field(..., min_items=2, max_items=settings.max_grades)
    candidates: list[Candidate] = Field(..., min_items=2, max_items=settings.max_candidates)
    description: Description
    ref: Ref
    date_created: datetime= Field(default_factory=datetime.now)
    date_modified: datetime= Field(default_factory=datetime.now)
    num_voters: int = Field(0, ge=0, le=settings.max_voters)
    date_start: datetime = Field(default_factory=datetime.now)
    date_end: datetime = Field(default_factory=_in_a_long_time)
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
            raise ArgumentsSchemaError("This election can not end")

        return value

#     @validator("grades")
#     def all_grades_have_unique_values_and_names(cls, grades: list[Grade]):
#         values = [g.value for g in grades]
#         if len(set(values)) != len(grades):
#             raise ArgumentsSchemaError("Two grades have the same value")
#    
#         names = [g.name for g in grades]
#         if len(set(names)) != len(grades):
#             raise ArgumentsSchemaError("Two grades have the same name")
# 
#         return grades
# 
#     @validator("candidates")
#     def all_candidates_have_unique_names(cls, candidates: list[Grade]):
#         names = [c.name for c in candidates]
#         if len(set(names)) != len(candidates):
#             raise ArgumentsSchemaError("Two candidates have the same name")
#    
#         return candidates
# 
    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class ElectionCreate(Election):
    invites: list[str] = []
    admin: str = ""

    def dict(self, *args, **kwargs):
        """
        Convert set into list to avoid an issue with SQLAlchemy
        """
        orig = super().dict(*args, **kwargs)
        adapted = {
            **orig,
           "grades": list(orig["grades"]),
           "candidates": list(orig["candidates"]),
        }
                
        assert "votes" not in adapted
        return adapted
