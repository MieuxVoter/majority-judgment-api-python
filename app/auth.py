import json
from collections.abc import Mapping
import typing as t
from jose import jws, JWSError
from . import errors
from .settings import settings


def jws_verify(token: str) -> Mapping[str, t.Any]:
    """
    Verify the content of a JWS token
    """
    try:
        data = jws.verify(token, settings.secret, algorithms=["HS256"])
    except JWSError:
        raise errors.UnauthorizedError("Can not decode token")

    if not isinstance(data, bytes):
        raise errors.BadRequestError("Ununderstandable token")

    try:
        return json.loads(data)
    except json.decoder.JSONDecodeError:
        raise errors.BadRequestError("Ununderstandable token")


def create_ballot_token(
    vote_ids: int | list[int],
    election_ref: str,
) -> str:
    if isinstance(vote_ids, int):
        vote_ids = [vote_ids]
    vote_ids = sorted(vote_ids)
    return jws.sign(
        {"votes": vote_ids, "election": election_ref},
        settings.secret,
        algorithm="HS256",
    )


def create_admin_token(
    election_ref: str,
) -> str:
    return jws.sign(
        {"admin": True, "election": election_ref},
        settings.secret,
        algorithm="HS256",
    )

def create_election_iam_token(
    election_ref: str,
    iam:str|list[str]
) -> str:
    if isinstance(iam, str):
        iam = [iam]

    return jws.sign(
        {"iam": iam, "election": election_ref},
        settings.secret,
        algorithm="HS256",
    )

# IAM

def can(iam:str|list[str], action:str) -> bool:
    """
    Check if the user has the right to perform the action
    """
    if isinstance(iam, str):
        iam = [iam]

    if action not in SPECIFIC_IAM_TO_ALLOWED:
        return False

    if action in iam:
        return True

    return any(instance in SPECIFIC_IAM_TO_ALLOWED[action] for instance in iam)

ADMIN= "admin"
GET_PROGRESS = "get_progress"
CAN_VIEW_RESULT = "can_view_result"
CAN_VIEW_DETAILED_RESULT = "can_view_detailed_result"

SPECIFIC_IAM_TO_ALLOWED = {
    ADMIN : [],  
    GET_PROGRESS : [ADMIN],
    CAN_VIEW_RESULT : [ADMIN, CAN_VIEW_DETAILED_RESULT],
    CAN_VIEW_DETAILED_RESULT : [ADMIN]
}