import typing as t
from datetime import datetime, timedelta, timezone
import dateutil.parser
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from pydantic_settings import SettingsConfigDict
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


class CandidateBase(BaseModel):
    model_config = SettingsConfigDict(from_attributes=True)	

    name: Name
    description: Description = ""
    image: Image = ""


class CandidateGet(CandidateBase):
    election_ref: str
    id: int


class CandidateUpdate(CandidateBase):
    id: int | None = None


class CandidateCreate(CandidateBase):
    #  When creating an election, we don't have access yet to the Candidate id
    pass


class GradeBase(BaseModel):
    model_config = SettingsConfigDict(from_attributes=True)	
    name: Name
    value: int = Field(ge=0, lt=settings.max_grades)
    description: Description = ""

class GradeGet(GradeBase):
    election_ref: str
    id: int


class GradeUpdate(GradeBase):
    id: int


class GradeCreate(GradeBase):
    #  When creating an election, we don't have access yet to the Candidate id
    pass


class VoteGet(BaseModel):
    model_config = SettingsConfigDict(from_attributes=True)	
    id: int
    election_ref: str
    candidate: CandidateGet | None = Field(default=None)
    grade: GradeGet | None = Field(default=None)


class VoteCreate(BaseModel):
    model_config = SettingsConfigDict(from_attributes=True)	
    candidate_id: int
    grade_id: int

def _in_a_long_time() -> datetime:
    """
    Provides the date in the future
    """
    return datetime.now(timezone.utc) + timedelta(weeks=10 * 52)

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

def _parse_date(value:datetime | int | str | None):
    if value is None:
        return None
    
    if isinstance(value, datetime):
        value_as_datetime = value
    elif isinstance(value, int):
        value_as_datetime = datetime.fromtimestamp(value)
    else:
        try:
            value_as_datetime = dateutil.parser.parse(value)
        except dateutil.parser.ParserError:
            value = value[: value.index("(")]
            value_as_datetime = dateutil.parser.parse(value)

    if value_as_datetime.tzinfo is None and not settings.sqlite:
        import datetime as dt
        local_tz = dt.datetime.now(dt.timezone.utc).astimezone().tzinfo
        value_as_datetime = value_as_datetime.replace(tzinfo=local_tz).astimezone(timezone.utc)
    elif value_as_datetime.tzinfo is not None:
        if settings.sqlite:
            value_as_datetime = value_as_datetime.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            value_as_datetime = value_as_datetime.astimezone(timezone.utc)

    return value_as_datetime

class ElectionBase(BaseModel):
    model_config = SettingsConfigDict(from_attributes=True, arbitrary_types_allowed=True)	

    name: Name
    description: Description = ""
    ref: Ref = ""
    date_start: datetime | int | str | None = Field(default_factory=_utc_now)
    date_end: datetime | int | str | None = Field(default_factory=_in_a_long_time)
    hide_results: bool = True
    restricted: bool = False
    auth_for_result: bool = False

    @field_validator("date_end", "date_start", mode="before")
    @classmethod
    def parse_date(cls, value):
        return _parse_date(value)

class ElectionGet(ElectionBase):
    force_close: bool = False
    grades: list[GradeGet] = Field(..., min_length=2, max_length=settings.max_grades)
    candidates: list[CandidateGet] = Field(
        ..., min_length=2, max_length=settings.max_candidates
    )


class ResultsGet(ElectionGet):
    grades: list[GradeGet] = Field(..., min_length=2, max_length=settings.max_grades)
    candidates: list[CandidateGet] = Field(
        ..., min_length=2, max_length=settings.max_candidates
    )
    merit_profile: dict[int, dict[int, int]]
    ranking: dict[int, int] = {}


class ElectionCreatedGet(ElectionGet):
    invites: list[str] = []
    admin: str = ""


class ElectionUpdatedGet(ElectionGet):
    invites: list[str] = []


class ElectionCreate(ElectionBase):
    grades: list[GradeBase] = Field(..., min_length=2, max_length=settings.max_grades)
    num_voters: int = Field(default=0, ge=0, le=settings.max_voters)
    candidates: list[CandidateBase] = Field(
        ..., min_length=2, max_length=settings.max_candidates
    )

    @field_validator("hide_results", "num_voters", "date_end")
    @classmethod
    def can_finish(cls, value: str, info: ValidationInfo):
        """
        Enforce that the election is finish-able
        """
        values = info.data

        if "hide_results" in values:
            hide_results = values["hide_results"]
        elif info.field_name == "hide_results":
            hide_results = value
        else:
            return value

        if "num_voters" in values:
            num_voters = values["num_voters"]
        elif info.field_name == "num_voters":
            num_voters = value
        else:
            return value

        if "date_end" in values:
            date_end = values["date_end"]
        elif info.field_name == "date_end":
            date_end = value
        else:
            return value

        if hide_results and num_voters == 0 and date_end is None:
            raise ArgumentsSchemaError("This election can not end")

        return value

    @field_validator("grades")
    @classmethod
    def all_grades_have_unique_values_and_names(cls, grades: list[GradeBase]):
        values = [g.value for g in grades]
        if len(set(values)) != len(grades):
            raise ArgumentsSchemaError("At least two grades have the same value")

        names = [g.name for g in grades]
        if len(set(names)) != len(grades):
            raise ArgumentsSchemaError("At least two grades have the same name")

        return grades

    @field_validator("candidates")
    @classmethod
    def all_candidates_have_unique_names(cls, candidates: list[CandidateBase]):
        names = [c.name for c in candidates]
        if len(set(names)) != len(candidates):
            raise ArgumentsSchemaError("At least two candidates have the same name")

        return candidates

class ElectionUpdate(BaseModel):
    ref: str
    name: Name | None = None
    description: Description | None = None
    date_start: datetime | int | str | None = None
    date_end: datetime | int | str | None = None
    hide_results: bool | None = None
    restricted: bool | None = None
    grades: list[GradeUpdate] | None = None
    num_voters: int | None = None
    force_close: bool | None = None
    candidates: list[CandidateUpdate] | None = None
    auth_for_result: bool | None = None

    @field_validator("date_end", "date_start", mode="before")
    @classmethod
    def parse_date(cls, value):
        return _parse_date(value)

    @field_validator("grades")
    @classmethod
    def all_grades_have_unique_values_and_names(cls, grades: list[GradeUpdate] | None):
        if grades is None:
            return grades

        grades = [grade for grade in grades if grade.id is not None]

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

    @field_validator("candidates")
    @classmethod
    def all_candidates_have_unique_names_and_ids(
        cls, candidates: list[CandidateUpdate] | None
    ):
        if candidates is None:
            return candidates

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


class Progress(BaseModel):
    num_voters: int | None
    num_voters_voted: int
