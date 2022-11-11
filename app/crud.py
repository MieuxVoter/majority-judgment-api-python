from sqlalchemy.orm import Session

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
            "elections",
            f"Several elections have the same primary keys {election_id}"
        )

    if elections_by_id.count() == 1:
        return elections_by_id.first()

    elections_by_ref = db.query(models.Election).filter(
        models.Election.ref == election_id
    )

    if elections_by_ref.count() > 1:
        raise errors.InconsistentDatabaseError(
                "elections", 
                f"Several elections have the same reference {election_id}")

    if elections_by_ref.count() == 1:
        return elections_by_ref.first()

    raise errors.NotFoundError("elections")



def create_election(db: Session, election: schemas.Election) -> schemas.ElectionCreate:
    params = election.dict()
    print(params)
    db_election = models.Election(**params)
    print("post")
    db.add(db_election)
    db.commit()
    db.refresh(db_election)

    # TODO JWT token for invites
    invites: list[str] = []

    # TODO JWT token for admin panel
    admin = ""

    created_election = schemas.ElectionCreate.from_orm(db_election)
    created_election.invites = invites
    created_election.admin = admin

    return created_election
