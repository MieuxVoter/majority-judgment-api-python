from datetime import datetime
import pytest
from pydantic.error_wrappers import ValidationError
from ..schemas import (
    GradeBase,
    GradeGet,
    ElectionCreate,
    CandidateBase,
    CandidateGet,
    VoteBase,
    ArgumentsSchemaError,
)
from ..settings import settings


def test_grade_default_values():
    """
    Can create a simple GradeBase
    """
    now = datetime.now()
    grade = GradeBase(name="foo", value=1)
    assert grade.name == "foo"
    assert grade.date_modified > now
    assert grade.date_modified >= grade.date_created

    # Automatic conversion helps to load data from the payload
    grade = GradeBase(name="foo", value=1.2, description="bar foo")
    assert grade.value == 1

    grade = GradeBase(name="foo", value="1", description="bar foo")
    assert grade.value == 1

    # Any field name is accepted
    grade = GradeBase(name="foo", value=1, foo="bar")


def test_grade_validation_value():
    """
    Check the constrained on the value field of a grade
    """
    with pytest.raises(ValidationError):
        # value must be a positive integer
        GradeBase(name="foo", value="bar", description="bar foo")

    with pytest.raises(ValidationError):
        GradeBase(name="foo", value=-1, description="bar foo")

    with pytest.raises(ValidationError):
        GradeBase(name="foo", value=settings.max_grades + 1, description="bar foo")


def test_grade_validation_description_name():
    """
    Check the constrained on the name and description fields of a grade
    """
    with pytest.raises(ValidationError):
        # name should be less than 256 characters
        GradeBase(name="f" * 256, value=1, description="bar foo")

    with pytest.raises(ValidationError):
        # name should be less than 1024 characters
        GradeBase(name="foo", value=1, description="b" * 1025)


def test_candidate_defaults():
    """
    Can create a simple CandidateBase
    """
    now = datetime.now()
    candidate = CandidateBase(name="foo")
    assert candidate.name == "foo"
    assert candidate.description == ""
    assert candidate.image == ""
    assert candidate.date_modified > now
    assert candidate.date_modified >= candidate.date_created


def test_vote():
    """
    Can create a simple VoteBase
    """
    now = datetime.now()
    candidate = CandidateGet(name="foo", id=1)
    grade = GradeGet(name="bar", value=1, id=2)
    vote = VoteBase(candidate=candidate, grade=grade)
    assert vote.candidate == candidate
    assert vote.grade == grade
    assert vote.date_modified > now
    assert vote.date_modified >= vote.date_created


def test_election():
    """
    Can create a simple VoteBase
    """
    now = datetime.now()
    candidate0 = CandidateBase(name="bar")
    candidate1 = CandidateBase(name="foo")
    grade1 = GradeBase(name="very good", value=2)
    grade0 = GradeBase(name="fair enough", value=1)
    election = ElectionCreate(
        name="test", grades=[grade0, grade1], candidates=[candidate1, candidate0]
    )
    assert election.candidates == [candidate1, candidate0]
    assert len(election.grades) == 2
    assert election.date_modified > now
    assert election.date_modified > election.date_created
    assert election.date_end > now
    assert election.date_end > election.date_start

    with pytest.raises(ArgumentsSchemaError):
        # grades should have different value
        grade2 = GradeBase(name="good", value=1)
        ElectionCreate(
            name="test", grades=[grade0, grade2], candidates=[candidate1, candidate0]
        )

    with pytest.raises(ArgumentsSchemaError):
        # candidates should have different names
        candidate2 = CandidateBase(name="foo")
        ElectionCreate(
            name="test", grades=[grade0, grade1], candidates=[candidate1, candidate2]
        )
