from datetime import datetime
from collections import defaultdict
from typing import DefaultDict
from sqlalchemy.orm import Session
from sqlalchemy import func, insert
from majority_judgment import majority_judgment
from . import models, schemas, errors
from .settings import settings
from .auth import create_ballot_token, create_admin_token, jws_verify


def get_election(db: Session, election_id: int):
    """
    Load an election given its ID or its ref
    """
    elections_by_id = db.query(models.Election).filter(
        models.Election.id == election_id
    )

    if elections_by_id.count() > 1:
        raise errors.InconsistentDatabaseError(
            "elections", f"Several elections have the same primary keys {election_id}"
        )

    if elections_by_id.count() == 1:
        return elections_by_id.first()

    elections_by_ref = db.query(models.Election).filter(
        models.Election.ref == election_id
    )

    if elections_by_ref.count() > 1:
        raise errors.InconsistentDatabaseError(
            "elections", f"Several elections have the same reference {election_id}"
        )

    if elections_by_ref.count() == 1:
        return elections_by_ref.first()

    raise errors.NotFoundError("elections")


def create_candidate(
    db: Session, candidate: schemas.CandidateRelational, commit: bool = False
) -> models.Candidate:
    params = candidate.dict()
    db_candidate = models.Candidate(**params)
    db.add(db_candidate)

    if commit:
        db.commit()
        db.refresh(db_candidate)

    return db_candidate


def create_grade(
    db: Session, grade: schemas.GradeRelational, commit: bool = False
) -> models.Grade:
    params = grade.dict()
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

    if commit:
        db.commit()
        db.refresh(db_election)

    return db_election


def create_invite_tokens(
    db: Session,
    election_id: int,
    num_candidates: int,
    num_voters: int,
) -> list[str]:
    now = datetime.now()
    params = {"date_created": now, "date_modified": now, "election_id": election_id}
    db_votes = [models.Vote(**params) for _ in range(num_voters * num_candidates)]
    db.bulk_save_objects(db_votes, return_defaults=True)
    vote_ids = [int(str(v.id)) for v in db_votes]
    tokens = [
        create_ballot_token(vote_ids[i::num_candidates], election_id)
        for i in range(num_voters)
    ]
    return tokens


def create_election(
    db: Session, election: schemas.ElectionCreate
) -> schemas.ElectionGet:
    # We create first the election
    # without candidates and grades
    db_election = _create_election_without_candidates_or_grade(db, election, True)

    # Then, we add separatly candidates and grades
    for candidate in election.candidates:
        params = candidate.dict()
        params["election_id"] = db_election.id
        candidate_rel = schemas.CandidateRelational(**params)
        create_candidate(db, candidate_rel, False)

    for grade in election.grades:
        params = grade.dict()
        params["election_id"] = db_election.id
        grade_rel = schemas.GradeRelational(**params)
        create_grade(db, grade_rel, False)

    db.commit()
    db.refresh(db_election)

    invites: list[str] = create_invite_tokens(
        db, int(str(db_election.id)), len(election.candidates), election.num_voters
    )

    admin = create_admin_token(int(str(db_election.id)))

    election_and_invites = schemas.ElectionAndInvitesGet.from_orm(db_election)
    election_and_invites.invites = invites
    election_and_invites.admin = admin

    return election_and_invites


def create_vote(db: Session, vote: schemas.BallotCreate) -> schemas.BallotGet:
    votes = vote.votes

    if votes == []:
        raise errors.BadRequestError("The ballot contains no vote")

    election_id = votes[0].election_id

    # Check if the election is open
    db_election = get_election(db, election_id)
    if db_election is None:
        raise errors.NotFoundError("Unknown election.")
    if db_election.restricted:
        raise errors.BadRequestError(
            "The election is restricted. You can not create new votes"
        )

    # Ideally, we would use RETURNING but it does not work yet for SQLite
    db_votes = [models.Vote(**v.dict()) for v in vote.votes]
    db.add_all(db_votes)
    db.commit()
    for v in db_votes:
        db.refresh(v)

    votes_get = [schemas.VoteGet.from_orm(v) for v in db_votes]
    vote_ids = [v.id for v in votes_get]
    token = create_ballot_token(vote_ids, election_id)
    return schemas.BallotGet(votes=votes_get, token=token)


def update_vote(db: Session, vote: schemas.BallotUpdate) -> schemas.BallotGet:
    votes = vote.votes
    token = vote.token

    if votes == []:
        raise errors.BadRequestError("The ballot contains no vote")

    election_id = votes[0].election_id

    # Check if the election exists
    db_election = get_election(db, election_id)
    if db_election is None:
        raise errors.NotFoundError("Unknown election.")

    db_votes = [models.Vote(**v.dict()) for v in vote.votes]
    db.bulk_save_objects(db_votes, return_defaults=True)

    votes_get = [schemas.VoteGet.from_orm(v) for v in db_votes]
    vote_ids = [v.id for v in votes_get]
    token = create_ballot_token(vote_ids, election_id)
    return schemas.BallotGet(votes=votes_get, token=token)


def get_votes(db: Session, token: str) -> schemas.BallotGet:
    data = jws_verify(token)
    vote_ids = data["votes"]
    election_id = data["election"]

    votes = db.query(models.Vote).filter(
        models.Vote.id.in_((vote_ids))
        & (models.Vote.candidate_id.is_not(None))
        & (models.Vote.election_id == election_id)
    )
    votes_get = [schemas.VoteGet.from_orm(v) for v in votes.all()]
    return schemas.BallotGet(token=token, votes=votes_get)


def get_results(db: Session, election_id: int) -> schemas.ResultsGet:
    db_election = get_election(db, election_id)

    query = db.query(
        models.Vote.candidate_id, models.Grade.value, func.count(models.Vote.id)
    )
    db_votes = (
        query.join(models.Vote.grade)
        .filter(models.Vote.election_id == election_id)
        .group_by(models.Vote.candidate_id, models.Vote.grade_id)
        .all()
    )
    ballots: DefaultDict[int, dict[int, int]] = defaultdict(dict)
    for candidate_id, grade_value, num_votes in db_votes:
        ballots[candidate_id][grade_value] = num_votes
    merit_profile = {
        c: [votes[value] for value in sorted(votes.keys(), reverse=True)]
        for c, votes in ballots.items()
    }

    ranking = majority_judgment(merit_profile)  # pyright: ignore

    results = schemas.ResultsGet.from_orm(db_election)

    results.ranking = ranking

    return results
