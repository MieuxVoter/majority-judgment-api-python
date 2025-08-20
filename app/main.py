import typing as t
import json
from fastapi import Depends, FastAPI, HTTPException, Request, Body, Header
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from jose.exceptions import JWEError, JWSError

from . import crud, models, schemas, errors
from .database import get_db, engine, Base
from .settings import settings

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # This overrides FastAPI's default 422 validation error handler
    # to produce our standardized error format.
    return JSONResponse(
        status_code=422,
        content={"error": "VALIDATION_ERROR", "message": str(exc)},
    )

@app.get("/")
async def main():
    return {"message": "Hello World"}


@app.exception_handler(errors.CustomError)
async def custom_error_exception_handler(request: Request, exc: errors.CustomError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code, "message": str(exc)},
    )

@app.exception_handler(schemas.ArgumentsSchemaError)
async def invalid_schema_exception_handler(
    request: Request, exc: schemas.ArgumentsSchemaError
):
    return JSONResponse(
        status_code=422,
        content={"error": "SCHEMA_VALIDATION_ERROR", "message": str(exc)},
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


@app.get("/elections/{election_ref}/progress", response_model=schemas.Progress)
def get_progress(
    election_ref: str, authorization: str = Header(), db: Session = Depends(get_db)
):
    token = authorization.split("Bearer ")[1]
    progress = crud.get_progress(db, election_ref, token)
    return progress


@app.post("/elections", response_model=schemas.ElectionCreatedGet)
def create_election(election: schemas.ElectionCreate, db: Session = Depends(get_db)):
    return crud.create_election(db=db, election=election)


@app.put("/elections", response_model=schemas.ElectionUpdatedGet)
def update_election(
    election: schemas.ElectionUpdate,
    authorization: str = Header(),
    db: Session = Depends(get_db),
):
    token = authorization.split("Bearer ")[1]
    return crud.update_election(db=db, election=election, token=token)


@app.post("/ballots", response_model=schemas.BallotGet)
def create_ballot(
    ballot: schemas.BallotCreate,
    db: Session = Depends(get_db),
):
    return crud.create_ballot(db=db, ballot=ballot)


@app.put("/ballots", response_model=schemas.BallotGet)
def update_ballot(
    ballot: schemas.BallotUpdate,
    authorization: str = Header(),
    db: Session = Depends(get_db),
):
    token = authorization.split("Bearer ")[1]
    return crud.update_ballot(db=db, ballot=ballot, token=token)


@app.get("/ballots", response_model=schemas.BallotGet)
def get_ballot(authorization: str = Header(), db: Session = Depends(get_db)):
    token = authorization.split("Bearer ")[1]
    return crud.get_ballot(db=db, token=token)


@app.get("/results/{election_ref}", response_model=schemas.ResultsGet)
def get_results(election_ref: str, authorization: t.Optional[str] = Header(default=None), db: Session = Depends(get_db)):
    token = authorization.split("Bearer ")[1] if authorization else None
    return crud.get_results(db=db, token=token, election_ref=election_ref)
