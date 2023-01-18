import typing as t
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator
from pydantic.fields import ModelField
from .settings import settings


class ArgumentsSchemaError(Exception):
    """
    An error occured on the arguments provided to a schema
    """


Name = t.Annotated[str, Field(min_length=1, max_length=255)]
Ref = t.Annotated[str, Field(..., max_length=255)]
Image = t.Annotated[str, Field(..., max_length=255)]
Description = t.Annotated[str, Field(..., max_length=1024)]
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


class CandidateBase(BaseModel):
    name: Name
    description: Description = ""
    image: Image = ""

    class Config:
        orm_mode = True


class CandidateGet(CandidateBase):
    election_ref: str
    id: int


class CandidateUpdate(CandidateBase):
    id: int


class CandidateCreate(CandidateBase):
    #  When creating an election, we don't have access yet to the Candidate id
    pass


class GradeBase(BaseModel):
    name: Name
    value: int = Field(ge=0, lt=settings.max_grades, pre=True)
    description: Description = ""

    class Config:
        orm_mode = True


class GradeGet(GradeBase):
    election_ref: str
    id: int


class GradeUpdate(GradeBase):
    id: int


class GradeCreate(GradeBase):
    #  When creating an election, we don't have access yet to the Candidate id
    pass


class VoteGet(BaseModel):
    id: int
    election_ref: str
    candidate: CandidateGet | None = Field(default=None)
    grade: GradeGet | None = Field(default=None)

    class Config:
        orm_mode = True


class VoteCreate(BaseModel):
    candidate_id: int
    grade_id: int

    class Config:
        orm_mode = True


def _in_a_long_time() -> datetime:
    """
    Provides the date in the future
    """
    return datetime.now() + timedelta(weeks=10 * 52)


class ElectionBase(BaseModel):
    name: Name
    description: Description = ""
    ref: Ref = ""
    date_start: datetime = Field(default_factory=datetime.now)
    date_end: datetime = Field(default_factory=_in_a_long_time)
    hide_results: bool = True
    restricted: bool = False

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class ElectionGet(ElectionBase):
    force_close: bool = False
    grades: list[GradeGet] = Field(..., min_items=2, max_items=settings.max_grades)
    candidates: list[CandidateGet] = Field(
        ..., min_items=2, max_items=settings.max_candidates
    )


class ResultsGet(ElectionGet):
    grades: list[GradeGet] = Field(..., min_items=2, max_items=settings.max_grades)
    candidates: list[CandidateGet] = Field(
        ..., min_items=2, max_items=settings.max_candidates
    )
    merit_profile: dict[int, dict[int, int]]
    ranking: dict[int, int] = {}


class ElectionCreatedGet(ElectionGet):
    invites: list[str] = []
    admin: str = ""


class ElectionUpdatedGet(ElectionGet):
    invites: list[str] = []


class ElectionCreate(ElectionBase):
    grades: list[GradeBase] = Field(..., min_items=2, max_items=settings.max_grades)
    num_voters: int = Field(0, ge=0, le=settings.max_voters)
    candidates: list[CandidateBase] = Field(
        ..., min_items=2, max_items=settings.max_candidates
    )

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

    @validator("grades")
    def all_grades_have_unique_values_and_names(cls, grades: list[GradeBase]):
        values = [g.value for g in grades]
        if len(set(values)) != len(grades):
            raise ArgumentsSchemaError("At least two grades have the same value")

        names = [g.name for g in grades]
        if len(set(names)) != len(grades):
            raise ArgumentsSchemaError("At least two grades have the same name")

        return grades

    @validator("candidates")
    def all_candidates_have_unique_names(cls, candidates: list[CandidateBase]):
        names = [c.name for c in candidates]
        if len(set(names)) != len(candidates):
            raise ArgumentsSchemaError("At least two candidates have the same name")

        return candidates


class ElectionUpdate(ElectionBase):
    ref: str
    grades: list[GradeUpdate] = Field(..., min_items=2, max_items=settings.max_grades)
    num_voters: int = Field(0, ge=0, le=settings.max_voters)
    force_close: bool = False
    candidates: list[CandidateUpdate] = Field(
        ..., min_items=2, max_items=settings.max_candidates
    )

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

    @validator("grades")
    def all_grades_have_unique_values_ids_and_names(cls, grades: list[GradeUpdate]):
        values = [g.value for g in grades]
        if len(set(values)) != len(grades):
            raise ArgumentsSchemaError("At least two grades have the same value")

        names = [g.name for g in grades]
        if len(set(names)) != len(grades):
            raise ArgumentsSchemaError("At least two grades have the same name")

        ids = [g.id for g in grades]
        if len(set(ids)) != len(ids):
            raise ArgumentsSchemaError("At least two grades have the same id")

        return grades

    @validator("candidates")
    def all_candidates_have_unique_names_and_ids(
        cls, candidates: list[CandidateUpdate]
    ):
        names = [c.name for c in candidates]
        if len(set(names)) != len(candidates):
            raise ArgumentsSchemaError("At least two candidates have the same name")

        ids = [c.id for c in candidates]
        if len(set(ids)) != len(ids):
            raise ArgumentsSchemaError("At least two candidates have the same id")

        return candidates


class BallotGet(BaseModel):
    votes: list[VoteGet]
    election: ElectionGet
    token: str


class BallotCreate(BaseModel):
    votes: list[VoteCreate]
    election_ref: str


class BallotUpdate(BaseModel):
    votes: list[VoteCreate]
