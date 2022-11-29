import typing as t
import json
from fastapi import Depends, FastAPI, HTTPException, Request, Body
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from jose import jwe, jws
from jose.exceptions import JWEError, JWSError

from . import crud, models, schemas, errors
from .database import get_db, engine
from .settings import settings

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def main():
    return {"message": "Hello World"}


@app.exception_handler(errors.NotFoundError)
async def not_found_exception_handler(request: Request, exc: errors.NotFoundError):
    return JSONResponse(
        status_code=404,
        content={"message": f"Oops! No {exc.name} were found."},
    )


@app.exception_handler(errors.UnauthorizedError)
async def unauthorized_exception_handler(request: Request, exc: errors.NotFoundError):
    return JSONResponse(
        status_code=401, content={"message": "Unautorized", "details": exc.name}
    )


@app.exception_handler(errors.BadRequestError)
async def bad_request_exception_handler(request: Request, exc: errors.NotFoundError):
    return JSONResponse(
        status_code=400,
        content={"message": f"Bad Request", "details": exc.name},
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


@app.get("/elections/{election_ref}", response_model=schemas.ElectionGet)
def read_election_all_details(election_ref: str, db: Session = Depends(get_db)):
    db_election = crud.get_election(db, election_ref)
    return db_election


@app.post("/elections", response_model=schemas.ElectionAndInvitesGet)
def create_election(election: schemas.ElectionCreate, db: Session = Depends(get_db)):
    return crud.create_election(db=db, election=election)


@app.post("/ballots", response_model=schemas.BallotGet)
def create_ballot(
    ballot: schemas.BallotCreate,
    db: Session = Depends(get_db),
):
    try:
        return crud.create_ballot(db=db, ballot=ballot)
    except JWSError:
        raise errors.UnauthorizedError("Unverified token")


@app.put("/ballots", response_model=schemas.BallotGet)
def update_ballot(vote: schemas.BallotUpdate, db: Session = Depends(get_db)):
    try:
        return crud.update_ballot(db=db, ballot=vote)
    except JWSError:
        raise errors.UnauthorizedError("Unverified token")


@app.get("/ballots/{token}", response_model=schemas.BallotGet)
def get_ballot(token: str, db: Session = Depends(get_db)):
    return crud.get_ballot(db=db, token=token)


@app.get("/results/{election_ref}", response_model=schemas.ResultsGet)
def get_results(election_ref: str, db: Session = Depends(get_db)):
    return crud.get_results(db=db, election_ref=election_ref)
