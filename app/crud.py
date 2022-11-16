from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func
from majority_judgment import majority_judgment
from . import models, schemas, errors


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


def create_election(
    db: Session, election: schemas.ElectionCreate
) -> schemas.ElectionGet:
    # We create first the election
    # without candidates and grades
    db_election = _create_election_without_candidates_or_grade(db, election, True)

    # Then, we add separatly candidates and grades
    for candidate in election.candidates:
        candidate_rel = schemas.CandidateRelational(
            **{**candidate.dict(), "election_id": db_election.id}
        )
        create_candidate(db, candidate_rel, False)

    for grade in election.grades:
        grade_rel = schemas.GradeRelational(
            **{**grade.dict(), "election_id": db_election.id}
        )
        create_grade(db, grade_rel, False)

    db.commit()
    db.refresh(db_election)
    # create_
    # TODO JWT token for invites
    invites: list[str] = []

    # TODO JWT token for admin panel
    admin = ""

    election_and_invites = schemas.ElectionAndInvitesGet.from_orm(db_election)
    election_and_invites.invites = invites
    election_and_invites.admin = admin

    return election_and_invites


def create_vote(db: Session, vote: schemas.VoteCreate) -> schemas.VoteGet:
    db_vote = models.Vote(**vote.dict())
    db.add(db_vote)

    db.commit()
    db.refresh(db_vote)

    return db_vote


def get_vote(db: Session, vote_id: int) -> schemas.VoteGet:
    # TODO check with JWT tokens the authorization
    votes_by_id = db.query(models.Vote).filter(models.Vote.id == vote_id)

    if votes_by_id.count() > 1:
        raise errors.InconsistentDatabaseError(
            "votes", f"Several votes have the same primary keys {vote_id}"
        )

    if votes_by_id.count() == 1:
        return votes_by_id.first()

    votes_by_ref = db.query(models.Vote).filter(models.Vote.ref == vote_id)

    if votes_by_ref.count() > 1:
        raise errors.InconsistentDatabaseError(
            "votes", f"Several votes have the same reference {vote_id}"
        )

    if votes_by_ref.count() == 1:
        return votes_by_ref.first()

    raise errors.NotFoundError("votes")


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
    ballots = defaultdict(dict)
    for candidate_id, grade_value, num_votes in db_votes:
        ballots[candidate_id][grade_value] = num_votes
    merit_profile = {
        c: [votes[value] for value in sorted(votes.keys(), reverse=True)]
        for c, votes in ballots.items()
    }

    ranking = majority_judgment(merit_profile)

    results = schemas.ResultsGet.from_orm(db_election)

    results.ranking = ranking

    return results
