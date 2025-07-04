from datetime import datetime
import random
import string
from collections import defaultdict
import typing as t
from sqlalchemy.orm import Session
from sqlalchemy import func
from majority_judgment import majority_judgment
from . import models, schemas, errors
from .auth import create_ballot_token, create_admin_token, jws_verify


def get_election(db: Session, election_ref_or_id: str):
    """
    Load an election given its ID or its ref
    """
    if election_ref_or_id.isnumeric():
        elections = db.query(models.Election).filter(
            models.Election.id == election_ref_or_id
        )
    else:
        elections = db.query(models.Election).filter(
            models.Election.ref == election_ref_or_id
        )

    if elections.count() > 1:
        raise errors.InconsistentDatabaseError(
            "elections",
            f"Several elections have the same primary keys {election_ref_or_id}",
        )

    if elections.count() == 1:
        return elections.first()

    raise errors.NotFoundError("elections")


def get_progress(db: Session, election_ref: str, token: str) -> schemas.Progress:
    """
    Load an election given its ID or its ref
    """
    payload = jws_verify(token)
    election_ref2 = payload["election"]

    if election_ref != election_ref2:
        raise errors.UnauthorizedError("Wrong election ref")
    
    # Check we can update the election
    if not payload["admin"]:
        raise errors.ForbiddenError("You are not allowed to manage the election")

    # Votes are provided for each candidate and each voter
    votes = db.query(models.Vote).filter(models.Vote.election_ref == election_ref)
    candidates = db.query(models.Candidate).filter(
        models.Candidate.election_ref == election_ref
    )

    num_votes = votes.count()
    num_candidates = candidates.count()
    num_voters = num_votes // num_candidates

    # Get number of voters who have voted (their grade is not null)
    voters_voted = votes.filter(models.Vote.grade != None)
    num_voters_voted = voters_voted.count() // num_candidates

    return schemas.Progress(
        num_voters=num_voters,
        num_voters_voted=num_voters_voted,
    )


def create_candidate(
    db: Session,
    candidate: schemas.CandidateCreate | schemas.CandidateUpdate,
    election_ref: str,
    commit: bool = False,
) -> models.Candidate:
    params = candidate.model_dump()
    params["election_ref"] = election_ref
    db_candidate = models.Candidate(**params)
    db.add(db_candidate)

    if commit:
        db.commit()
        db.refresh(db_candidate)

    return db_candidate


def create_grade(
    db: Session,
    grade: schemas.GradeCreate,
    election_ref: str,
    commit: bool = False,
) -> models.Grade:
    params = grade.model_dump()
    params["election_ref"] = election_ref
    db_grade = models.Grade(**params)
    db.add(db_grade)

    if commit:
        db.commit()
        db.refresh(db_grade)

    return db_grade


def update_candidates(
    db: Session,
    candidates: list[schemas.CandidateUpdate],
    db_candidates: list[models.Candidate] | None = None,
    commit: bool = False,
) -> list[models.Candidate]:
    candidate_by_id = {c.id: c for c in candidates}
    candidate_ids = list(candidate_by_id.keys())

    if db_candidates is None:
        db_candidates = (
            db.query(models.Candidate)
            .filter(models.Candidate.id.in_(candidate_ids))
            .all()
        )

    if len(candidate_ids) != len(db_candidates):
        raise errors.NotFoundError("Can not find all candidates")

    for db_candidate in db_candidates:
        cid = int(str(db_candidate.id))
        params = candidate_by_id[cid].model_dump()
        del params["id"]
        for key, value in params.items():
            setattr(db_candidate, key, value)

    if commit:
        db.commit()
        for db_candidate in db_candidates:
            db.refresh(db_candidate)

    return db_candidates


def update_grades(
    db: Session,
    grades: list[schemas.GradeUpdate],
    db_grades: list[models.Grade] | None = None,
    commit: bool = False,
) -> list[models.Grade]:
    grade_by_id = {g.id: g for g in grades}
    grade_ids = list(grade_by_id.keys())

    if db_grades is None:
        db_grades = db.query(models.Grade).filter(models.Grade.id.in_(grade_ids)).all()

    if len(grade_ids) != len(db_grades):
        raise errors.NotFoundError("Can not find all grades")

    for db_grade in db_grades:
        gid = int(str(db_grade.id))
        params = grade_by_id[gid].model_dump()
        del params["id"]
        for key, value in params.items():
            setattr(db_grade, key, value)

    if commit:
        db.commit()
        for db_grade in db_grades:
            db.refresh(db_grade)

    return db_grades


def _create_election_without_candidates_or_grade(
    db: Session, election: schemas.ElectionBase, commit: bool
) -> models.Election:
    params = election.model_dump()
    del params["candidates"]
    del params["grades"]
    
    if params.get("date_start") is not None and params.get("date_end") is not None:
        if params["date_start"] >= params["date_end"]:
            raise errors.ForbiddenError(
                "The start date must be before the end date of the election"
            )

    db_election = models.Election(**params)
    db.add(db_election)

    # Generate a unique ref to the election
    success = False
    for i in range(10):
        ref = generate_election_ref()
        setattr(db_election, "ref", ref)
        if not _check_if_ref_exists(db, ref):
            success = True
            break

    if not success:
        raise errors.InconsistentDatabaseError(
            name="elections", details="Cannot find a unique ref"
        )

    if commit:
        db.commit()
        db.refresh(db_election)

    return db_election


def create_invite_tokens(
    db: Session,
    election_ref: str,
    num_candidates: int,
    num_voters: int,
) -> list[str]:
    if num_voters <= 0:
        return []
        
    _check_election_is_not_ended(get_election(db, election_ref))
    now = datetime.now()
    params = {"date_created": now, "date_modified": now, "election_ref": election_ref}
    db_votes = [models.Vote(**params) for _ in range(num_voters * num_candidates)]
    db.bulk_save_objects(db_votes, return_defaults=True)
    db.commit()
    vote_ids = [int(str(v.id)) for v in db_votes]
    tokens = [
        create_ballot_token(vote_ids[i::num_voters], election_ref)
        for i in range(num_voters)
    ]
    return tokens


def generate_election_ref(length: int = 10):
    return "".join(random.choices(string.ascii_lowercase, k=length))


def _check_if_ref_exists(db: Session, ref: str):
    results = db.query(models.Election).filter(models.Election.ref == ref).count()
    return results != 0


def create_election(
    db: Session, election: schemas.ElectionCreate
) -> schemas.ElectionGet:
    # We create first the election
    # without candidates and grades
    db_election = _create_election_without_candidates_or_grade(db, election, True)

    if db_election is None:
        raise errors.InconsistentDatabaseError("Can not create election")
    
    election_ref = str(db_election.ref)

    # Then, we add separatly candidates and grades
    for candidate in election.candidates:
        params = candidate.model_dump()
        candidate = schemas.CandidateCreate(**params)
        create_candidate(db, candidate, election_ref, False)

    for grade in election.grades:
        params = grade.model_dump()
        grade = schemas.GradeCreate(**params)
        create_grade(db, grade, election_ref, False)

    db.commit()
    db.refresh(db_election)

    invites: list[str] = create_invite_tokens(
        db, str(db_election.ref), len(election.candidates), election.num_voters
    )

    admin = create_admin_token(str(db_election.ref))

    created_election = schemas.ElectionCreatedGet.model_validate(db_election)
    created_election.invites = invites
    created_election.admin = admin

    return created_election


def update_election(
    db: Session, election: schemas.ElectionUpdate, token: str
) -> schemas.ElectionUpdatedGet:
    payload = jws_verify(token)
    election_ref = payload["election"]

    # Check we can update the election
    if not payload["admin"]:
        raise errors.ForbiddenError("You are not allowed to manage the election")

    if election_ref != election.ref:
        raise errors.ForbiddenError("Wrong election ref")

    db_election = get_election(db, election_ref)

    if db_election is None:
        raise errors.NotFoundError("elections")

    if election.date_start is not None and election.date_end is None and db_election.date_end is not None:
        if schemas.parse_date(election.date_start) > schemas.parse_date(db_election.date_end):
            raise errors.ForbiddenError(
                "The start date must be before the end date of the election"
            )
    elif election.date_end is not None and election.date_start is None:
        if schemas.parse_date(election.date_end) < schemas.parse_date(db_election.date_start):
            raise errors.ForbiddenError(
                "The end date must be after the start date of the election"
            )

    if (
        election.restricted is not None
        and bool(db_election.restricted) != election.restricted
    ):
        raise errors.ForbiddenError("You can't edit restrictions")

    if (
        election.num_voters is not None
        and election.num_voters > 0
        and not bool(db_election.restricted)
    ):
        raise errors.ForbiddenError(
            "You can't invite voters on a non-restricted election"
        )

    # Create new candidates (those whose Id is None)
    if election.candidates is not None:
        for candidate in election.candidates:
            if candidate.id is None:
                db_candidate = create_candidate(db, candidate, election_ref, True)
                candidate.id = int(str(db_candidate.id))

        # Check that candidates look fine
        candidate_ids = {c.id for c in election.candidates}
        db_candidate_ids = {c.id for c in db_election.candidates}
        if candidate_ids != db_candidate_ids:
            raise errors.ForbiddenError("You must have the same candidate ids")

    if election.grades is not None:
        grade_ids = {c.id for c in election.grades}
        db_grade_ids = {c.id for c in db_election.grades}
        if grade_ids != db_grade_ids:
            raise errors.ForbiddenError("You must have the same grade ids")

    # Update the candidates and grades
    if election.candidates is not None:
        update_candidates(db, election.candidates, db_election.candidates)
    if election.grades is not None:
        update_grades(db, election.grades, db_election.grades)

    for key in [
        "name",
        "description",
        "date_start",
        "date_end",
        "hide_results",
        "force_close",
        "auth_for_result",
    ]:
        if getattr(election, key) is None:
            continue
        if getattr(db_election, key) != getattr(election, key):
            setattr(db_election, key, getattr(election, key))

    db.commit()
    db.refresh(db_election)

    updated_election = schemas.ElectionUpdatedGet.model_validate(db_election)

    if election.num_voters is not None:
        updated_election.invites = create_invite_tokens(
            db, str(db_election.ref), len(db_election.candidates), election.num_voters
        )

    return updated_election


def _check_ballot_is_consistent(
    election: schemas.ElectionGet, ballot: schemas.BallotCreate
):
    votes_by_candidate = {
        c.id: [v for v in ballot.votes if v.candidate_id == c.id]
        for c in election.candidates
    }
    if not all(len(votes) == 1 for votes in votes_by_candidate.values()):
        raise errors.ForbiddenError("Unconsistent ballot")


def create_ballot(db: Session, ballot: schemas.BallotCreate) -> schemas.BallotGet:
    if ballot.votes == []:
        raise errors.ForbiddenError("The ballot contains no vote")

    db_election = _check_public_election(db, ballot.election_ref)
    election = schemas.ElectionGet.model_validate(db_election)

    _check_election_is_started(db_election)
    _check_election_is_not_ended(db_election)

    _check_items_in_election(
        db,
        [v.candidate_id for v in ballot.votes],
        ballot.election_ref,
        models.Candidate,
    )
    _check_items_in_election(
        db, [v.grade_id for v in ballot.votes], ballot.election_ref, models.Grade
    )
    _check_ballot_is_consistent(election, ballot)

    # Ideally, we would use RETURNING but it does not work yet for SQLite
    db_votes = [
        models.Vote(**v.model_dump(), election_ref=ballot.election_ref) for v in ballot.votes
    ]
    db.add_all(db_votes)
    db.commit()
    for v in db_votes:
        db.refresh(v)

    votes_get = [schemas.VoteGet.model_validate(v) for v in db_votes]
    vote_ids = [v.id for v in votes_get]
    token = create_ballot_token(vote_ids, ballot.election_ref)
    return schemas.BallotGet(votes=votes_get, token=token, election=election)


def _check_public_election(db: Session, election_ref: str):
    # Check if the election is open
    db_election = get_election(db, election_ref)
    if db_election is None:
        raise errors.NotFoundError("elections")
    if db_election.restricted:
        raise errors.ForbiddenError(
            "The election is restricted. You can not create new votes"
        )
    return db_election

def _check_election_is_started(election: models.Election):
    """
    Check that the election is started.
    If it is not, raise an error.
    """
    if election.date_start is not None and election.date_start > datetime.now():
        raise errors.ForbiddenError("The election has not started yet. You can not create votes")

def _check_election_is_not_ended(election: models.Election):
    """
    Check that the election is not ended.
    If it is, raise an error.
    """
    if election.date_end is not None and election.date_end < datetime.now():
        raise errors.ForbiddenError("The election has ended. You can not create new votes")
    if election.force_close:
        raise errors.ForbiddenError("The election is closed. You can not create or update votes")    

def _check_items_in_election(
    db: Session,
    ids: t.Sequence[int],
    election_ref: str,
    model: t.Type[models.Grade | models.Candidate],
):
    """
    Check the items are related to the election.
    """
    unique_ids = list(set(ids))
    num_items = (
        db.query(model)
        .filter(model.id.in_(unique_ids) & (model.election_ref == election_ref))
        .count()
    )
    if num_items != len(unique_ids):
        raise errors.ForbiddenError(
            "Asking for resources related to a different election"
        )


def update_ballot(
    db: Session, ballot: schemas.BallotUpdate, token: str
) -> schemas.BallotGet:
    if ballot.votes == []:
        raise errors.BadRequestError("The ballot contains no vote")

    payload = jws_verify(token)
    election_ref = payload["election"]
    vote_ids: list[int] = list(set(payload["votes"]))

    # Check if the election exists
    db_election = get_election(db, election_ref)
    
    if db_election is None:
        raise errors.NotFoundError("elections")

    _check_election_is_started(db_election)
    _check_election_is_not_ended(db_election)

    if len(ballot.votes) != len(vote_ids):
        raise errors.ForbiddenError("Edit all votes at once.")

    _check_items_in_election(
        db, [v.candidate_id for v in ballot.votes], election_ref, models.Candidate
    )
    _check_items_in_election(
        db, [v.grade_id for v in ballot.votes], election_ref, models.Grade
    )

    # TODO Can we optimize it with a bulk update?
    db_votes = (
        db.query(models.Vote)
        .filter(
            models.Vote.id.in_(vote_ids)
        )  # & (models.Vote.election_ref == election_ref))
        .all()
    )

    if len(db_votes) != len(vote_ids):
        raise errors.NotFoundError("votes")

    election = schemas.ElectionGet.model_validate(db_votes[0].election)

    for vote, db_vote in zip(ballot.votes, db_votes):
        if db_vote.election_ref != election_ref:
            raise errors.BadRequestError("Wrong election id")
        setattr(db_vote, "candidate_id", vote.candidate_id)
        setattr(db_vote, "grade_id", vote.grade_id)
    db.commit()

    votes_get = [schemas.VoteGet.model_validate(v) for v in db_votes]
    token = create_ballot_token(vote_ids, election_ref)
    return schemas.BallotGet(votes=votes_get, token=token, election=election)


def get_ballot(db: Session, token: str) -> schemas.BallotGet:
    data = jws_verify(token)
    vote_ids = data["votes"]
    election_ref = data["election"]

    votes = db.query(models.Vote).filter(
        models.Vote.id.in_((vote_ids))
        & (models.Vote.candidate_id.is_not(None))
        & (models.Vote.election_ref == election_ref)
    )

    db_votes = list(votes.all())

    if db_votes == []:
        raise errors.NotFoundError("votes")

    election = db_votes[0].election

    votes_get = [schemas.VoteGet.model_validate(v) for v in votes.all()]
    return schemas.BallotGet(token=token, votes=votes_get, election=election)


def get_results(db: Session, election_ref: str, token: t.Optional[str]) -> schemas.ResultsGet:
    db_election = get_election(db, election_ref)
    if db_election is None:
        raise errors.NotFoundError("elections")

    if db_election.auth_for_result:
        if token is None:
            raise errors.UnauthorizedError("Election require auth for result, you need to set Authentication header")
        
        payload = jws_verify(token)
        
        if payload["election"] != election_ref:
            raise errors.UnauthorizedError("Wrong authentication for this election")

    if (
        db_election.hide_results
        and (db_election.date_end is not None and db_election.date_end > datetime.now())
        and not db_election.force_close
    ):
        raise errors.ForbiddenError("The election is not closed")

    query = db.query(
        models.Vote.candidate_id, models.Grade.value, func.count(models.Vote.id)
    )
    db_res = (
        query.join(models.Vote.grade)
        .join(models.Vote.candidate)
        .filter(models.Vote.election_ref == db_election.ref)
        .group_by(models.Vote.candidate_id, models.Grade.value)
        .all()
    )

    if db_res == []:
        raise errors.NoRecordedVotes()

    ballots: t.DefaultDict[int, dict[int, int]] = defaultdict(dict)
    for candidate_id, grade_value, num_votes in db_res:
        ballots[candidate_id][grade_value] = num_votes

    merit_profile2 = {
        c: {value: votes[value] for value in votes.keys()}
        for c, votes in ballots.items()
    }

    merit_profile:dict[int, list[int]] = {
        c: sorted(sum([[value] * votes[value] for value in votes.keys()], []))
        for c, votes in ballots.items()
    }

    ranking = majority_judgment(merit_profile)  # pyright: ignore
    db_election.ranking = ranking
    db_election.merit_profile = merit_profile2

    results = schemas.ResultsGet.model_validate(db_election)

    return results
