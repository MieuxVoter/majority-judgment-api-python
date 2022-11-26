from datetime import datetime
import pytest
from pydantic.error_wrappers import ValidationError
from ..schemas import (
    GradeCreate,
    GradeGet,
    ElectionCreate,
    CandidateCreate,
    CandidateGet,
    VoteGet,
    ArgumentsSchemaError,
)
from ..settings import settings


def test_grade_default_values():
    """
    Can create a simple GradeBase
    """
    now = datetime.now()
    grade = GradeCreate(name="foo", value=1, election_id=0)
    assert grade.name == "foo"

    # Automatic conversion helps to load data from the payload
    grade = GradeCreate(name="foo", value=1.2, description="bar foo")  # type: ignore
    assert grade.value == 1

    grade = GradeCreate(name="foo", value="1", description="bar foo")  # type: ignore
    assert grade.value == 1

    # Any field name is accepted
    grade = GradeCreate(name="foo", value=1, foo="bar")  # type: ignore


def test_grade_validation_value():
    """
    Check the constrained on the value field of a grade
    """
    with pytest.raises(ValidationError):
        # value must be a positive integer
        GradeCreate(name="foo", value="bar", description="bar foo")  # type: ignore

    with pytest.raises(ValidationError):
        GradeCreate(name="foo", value=-1, description="bar foo")

    with pytest.raises(ValidationError):
        GradeCreate(
            election_id=0,
            name="foo",
            value=settings.max_grades + 1,
            description="bar foo",
        )


def test_grade_validation_description_name():
    """
    Check the constrained on the name and description fields of a grade
    """
    with pytest.raises(ValidationError):
        # name should be less than 256 characters
        GradeCreate(name="f" * 256, value=1, description="bar foo")

    with pytest.raises(ValidationError):
        # name should be less than 1024 characters
        GradeCreate(name="foo", value=1, description="b" * 1025)


def test_candidate_defaults():
    """
    Can create a simple CandidateBase
    """
    now = datetime.now()
    candidate = CandidateCreate(name="foo")
    assert candidate.name == "foo"
    assert candidate.description == ""
    assert candidate.image == ""


def test_vote():
    """
    Can create a simple VoteGet
    """
    now = datetime.now()
    candidate = CandidateGet(name="foo", id=1, election_id=0)
    grade = GradeGet(name="bar", value=1, id=2, election_id=0)
    vote = VoteGet(candidate=candidate, grade=grade, id=1, election_id=0)
    assert vote.candidate == candidate
    assert vote.grade == grade


def test_election():
    """
    Can create a simple VoteGet
    """
    now = datetime.now()
    candidate0 = CandidateCreate(name="bar")
    candidate1 = CandidateCreate(name="foo")
    grade1 = GradeCreate(name="very good", value=2)
    grade0 = GradeCreate(name="fair enough", value=1)
    election = ElectionCreate(
        name="test", grades=[grade0, grade1], candidates=[candidate1, candidate0]
    )
    assert election.candidates == [candidate1, candidate0]
    assert len(election.grades) == 2
    assert election.date_end > now
    assert election.date_end > election.date_start

    with pytest.raises(ArgumentsSchemaError):
        # grades should have different value
        grade2 = GradeCreate(name="good", value=1)
        ElectionCreate(
            name="test", grades=[grade0, grade2], candidates=[candidate1, candidate0]
        )

    with pytest.raises(ArgumentsSchemaError):
        # candidates should have different names
        candidate2 = CandidateCreate(name="foo")
        ElectionCreate(
            name="test", grades=[grade0, grade1], candidates=[candidate1, candidate2]
        )
