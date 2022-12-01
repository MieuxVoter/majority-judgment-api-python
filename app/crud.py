from datetime import datetime
import random
import string
from collections import defaultdict
import typing as t
from sqlalchemy.orm import Session
from sqlalchemy import func, insert
from majority_judgment import majority_judgment
from . import models, schemas, errors
from .settings import settings
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


def create_candidate(
    db: Session,
    candidate: schemas.CandidateCreate,
    election_ref: str,
    commit: bool = False,
) -> models.Candidate:
    params = candidate.dict()
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
    params = grade.dict()
    params["election_ref"] = election_ref
    db_grade = models.Grade(**params)
    db.add(db_grade)

    if commit:
        db.commit()
        db.refresh(db_grade)

    return db_grade


def _create_election_without_candidates_or_grade(
    db: Session, election: schemas.ElectionBase, commit: bool
) -> models.Election:
    params = election.dict()
    del params["candidates"]
    del params["grades"]

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
        params = candidate.dict()
        candidate = schemas.CandidateCreate(**params)
        create_candidate(db, candidate, election_ref, False)

    for grade in election.grades:
        params = grade.dict()
        grade = schemas.GradeCreate(**params)
        create_grade(db, grade, election_ref, False)

    db.commit()
    db.refresh(db_election)

    invites: list[str] = create_invite_tokens(
        db, str(db_election.ref), len(election.candidates), election.num_voters
    )

    admin = create_admin_token(str(db_election.ref))

    election_and_invites = schemas.ElectionAndInvitesGet.from_orm(db_election)
    election_and_invites.invites = invites
    election_and_invites.admin = admin

    return election_and_invites


def create_ballot(db: Session, ballot: schemas.BallotCreate) -> schemas.BallotGet:
    if ballot.votes == []:
        raise errors.BadRequestError("The ballot contains no vote")

    db_election = _check_public_election(db, ballot.election_ref)
    election = schemas.ElectionGet.from_orm(db_election)

    _check_item_in_election(
        db,
        [v.candidate_id for v in ballot.votes],
        ballot.election_ref,
        models.Candidate,
    )
    _check_item_in_election(
        db, [v.grade_id for v in ballot.votes], ballot.election_ref, models.Grade
    )

    # Ideally, we would use RETURNING but it does not work yet for SQLite
    db_votes = [
        models.Vote(**v.dict(), election_ref=ballot.election_ref) for v in ballot.votes
    ]
    db.add_all(db_votes)
    db.commit()
    for v in db_votes:
        db.refresh(v)

    votes_get = [schemas.VoteGet.from_orm(v) for v in db_votes]
    vote_ids = [v.id for v in votes_get]
    token = create_ballot_token(vote_ids, ballot.election_ref)
    return schemas.BallotGet(votes=votes_get, token=token, election=election)


def _check_public_election(db: Session, election_ref: str):
    # Check if the election is open
    db_election = get_election(db, election_ref)
    if db_election is None:
        raise errors.NotFoundError("elections")
    if db_election.restricted:
        raise errors.BadRequestError(
            "The election is restricted. You can not create new votes"
        )
    return db_election


def _check_item_in_election(
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
        raise errors.BadRequestError(
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

    if len(ballot.votes) != len(vote_ids):
        raise errors.BadRequestError("Edit all votes at once.")

    _check_item_in_election(
        db, [v.candidate_id for v in ballot.votes], election_ref, models.Candidate
    )
    _check_item_in_election(
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

    election = schemas.ElectionGet.from_orm(db_votes[0].election)

    for vote, db_vote in zip(ballot.votes, db_votes):
        if db_vote.election_ref != election_ref:
            raise errors.BadRequestError("Wrong election id")
        setattr(db_vote, "candidate_id", vote.candidate_id)
        setattr(db_vote, "grade_id", vote.grade_id)
    db.commit()

    votes_get = [schemas.VoteGet.from_orm(v) for v in db_votes]
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

    votes_get = [schemas.VoteGet.from_orm(v) for v in votes.all()]
    return schemas.BallotGet(token=token, votes=votes_get, election=election)


def get_results(db: Session, election_ref: str) -> schemas.ResultsGet:
    db_election = get_election(db, election_ref)
    if db_election is None:
        raise errors.NotFoundError("elections")

    query = db.query(
        models.Vote.candidate_id, models.Grade.value, func.count(models.Vote.id)
    )
    db_votes = (
        query.join(models.Vote.grade)
        .filter(models.Vote.election_ref == db_election.ref)
        .group_by(models.Vote.candidate_id, models.Vote.grade_id)
        .all()
    )
    ballots: t.DefaultDict[int, dict[int, int]] = defaultdict(dict)
    for candidate_id, grade_value, num_votes in db_votes:
        ballots[candidate_id][grade_value] = num_votes
    merit_profile = {
        c: [votes[value] for value in sorted(votes.keys(), reverse=True)]
        for c, votes in ballots.items()
    }

    ranking = majority_judgment(merit_profile)  # pyright: ignore
    db_election.ranking = ranking
    db_election.merit_profile = merit_profile

    results = schemas.ResultsGet.from_orm(db_election)

    return results
