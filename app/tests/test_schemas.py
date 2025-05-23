from datetime import datetime
import pytest
from pydantic import ValidationError
import dateutil.parser
from ..schemas import (
    GradeCreate,
    GradeGet,
    ElectionCreate,
    CandidateCreate,
    CandidateGet,
    Progress,
    VoteGet,
    ArgumentsSchemaError,
)
from ..settings import settings


def test_grade_default_values():
    """
    Can create a simple GradeBase
    """
    grade = GradeCreate(name="foo", value=1)
    assert grade.name == "foo"

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
    candidate = CandidateCreate(name="foo")
    assert candidate.name == "foo"
    assert candidate.description == ""
    assert candidate.image == ""


def test_vote():
    """
    Can create a simple VoteGet
    """
    candidate = CandidateGet(name="foo", id=1, election_ref="bar")
    grade = GradeGet(name="bar", value=1, id=2, election_ref="bar")
    vote = VoteGet(candidate=candidate, grade=grade, id=1, election_ref="bar")
    assert vote.candidate == candidate
    assert vote.grade == grade

def _to_datetime(value):
    if isinstance(value, datetime):
        return value
    elif isinstance(value, int):
        return datetime.fromtimestamp(value)
    elif isinstance(value, str):
        try:
            return dateutil.parser.parse(value)
        except:
            # Gérer les erreurs de parsing
            pass
    # Valeur par défaut ou erreur
    return None

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

    if _to_datetime(election.date_end) is None:
        raise ArgumentsSchemaError("date_end is None")

    assert _to_datetime(election.date_end) > _to_datetime(election.date_start)

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


def test_election_date_string():
    """
    Can create an Election with custom date
    """
    candidate0 = CandidateCreate(name="bar")
    candidate1 = CandidateCreate(name="foo")
    grade1 = GradeCreate(name="very good", value=2)
    grade0 = GradeCreate(name="fair enough", value=1)
    election = ElectionCreate(
        name="test",
        grades=[grade0, grade1],
        candidates=[candidate1, candidate0],
        date_end="Tue Mar 28 2023 09:23:54 GMT+0200 (Central European Summer Time)",
        date_start="Tue Mar 27 2023 09:23:54 GMT+0200 (Central European Summer Time)",
    )
    assert election.candidates == [candidate1, candidate0]
    assert len(election.grades) == 2

    if _to_datetime(election.date_end) is None:
        raise ArgumentsSchemaError("date_end is None")
    assert _to_datetime(election.date_end) > _to_datetime(election.date_start)


def test_election_date_int():
    """
    Can create an Election with custom date
    """
    candidate0 = CandidateCreate(name="bar")
    candidate1 = CandidateCreate(name="foo")
    grade1 = GradeCreate(name="very good", value=2)
    grade0 = GradeCreate(name="fair enough", value=1)
    election = ElectionCreate(
        name="test",
        grades=[grade0, grade1],
        candidates=[candidate1, candidate0],
        date_start=167947177,
        date_end=167947178,
    )
    assert election.candidates == [candidate1, candidate0]
    assert len(election.grades) == 2

    if _to_datetime(election.date_end) is None:
        raise ArgumentsSchemaError("date_end is None")
    assert _to_datetime(election.date_end) > _to_datetime(election.date_start)


def test_progress():
    """
    Can create a simple Progress
    """
    progress = Progress(num_voters=0, num_voters_voted=0)
    assert progress.num_voters == 0
