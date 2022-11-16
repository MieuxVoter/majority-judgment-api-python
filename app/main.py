import typing as t
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from . import crud, models, schemas, errors
from .database import get_db, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.exception_handler(errors.NotFoundError)
async def not_found_exception_handler(request: Request, exc: errors.NotFoundError):
    return JSONResponse(
        status_code=404,
        content={"message": f"Oops! No {exc.name} were found."},
    )


@app.exception_handler(errors.InconsistentDatabaseError)
async def inconsistent_database_exception_handler(
    request: Request, exc: errors.InconsistentDatabaseError
):
    return JSONResponse(
        status_code=500,
        content={
            "message": f"A serious error has occured with {exc.name}. {exc.details or ''}"
        },
    )


@app.get("/liveness")
def read_root():
    return "OK"


@app.get("/elections/{election_id}", response_model=schemas.ElectionGet)
def read_election_all_details(election_id: int, db: Session = Depends(get_db)):
    db_election = crud.get_election(db, election_id=election_id)
    return db_election


@app.post("/elections", response_model=schemas.ElectionGet)
def create_election(election: schemas.ElectionCreate, db: Session = Depends(get_db)):
    return crud.create_election(db=db, election=election)


@app.post("/votes", response_model=schemas.VoteGet)
def create_vote(vote: schemas.VoteCreate, db: Session = Depends(get_db)):
    return crud.create_vote(db=db, vote=vote)


@app.get("/votes/{vote_id}", response_model=schemas.VoteGet)
def get_vote(vote_id: int, db: Session = Depends(get_db)):
    # TODO assert with a JWT token that we are allowed to read the vote
    return crud.get_vote(db=db, vote_id=vote_id)


@app.get("/results/{election_id}", response_model=schemas.ResultsGet)
def get_results(election_id: int, db: Session = Depends(get_db)):
    return crud.get_results(db=db, election_id=election_id)
