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


def is_pydantic(obj: object):
    """ Checks whether an object is pydantic. """
    return type(obj).__class__.__name__ == "ModelMetaclass"


def parse_pydantic_schema(schema):
    """
        Iterates through pydantic schema and parses nested schemas
        to a dictionary containing SQLAlchemy models.
        Only works if nested schemas have specified the Meta.orm_model.
    """
    parsed_schema = dict(schema)
    for key, value in parsed_schema.items():
        try:
            if isinstance(value, list) and len(value):
                if is_pydantic(value[0]):
                    parsed_schema[key] = [schema.Meta.orm_model(**schema.dict()) for schema in value]
            else:
                if is_pydantic(value):
                    parsed_schema[key] = value.Meta.orm_model(**value.dict())
        except AttributeError:
            raise AttributeError("Found nested Pydantic model but Meta.orm_model was not specified.")
    return parsed_schema



def create_candidate(
    db: Session,
    candidate: schemas.Candidate
    commit: bool = False
) -> schemas.Candidate:
    params = candidate.dict()
    db_election = models.Candidate(**params)
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


def _create_election_without_candidates_or_grade(db: Session, election: schemas.Election, commit: bool) -> models.Election:
    # We create first the election
    # without candidates and grades
    params = election.dict()
    del params['candidates']
    del params['grades']

    db_election = models.Election(params)
    db.add(db_election)

    if commit:
        db.commit()
        db.refresh(db_election)

    return db_election


def create_election(db: Session, election: schemas.Election) -> schemas.ElectionCreate:
    db_election = _create_election_without_candidates_or_grade(db, election, True)

    # Then, we add separatly candidates and grades
    create_
    # TODO JWT token for invites
    invites: list[str] = []

    # TODO JWT token for admin panel
    admin = ""

    created_election = schemas.ElectionCreate.from_orm(db_election)
    created_election.invites = invites
    created_election.admin = admin

    return created_election
