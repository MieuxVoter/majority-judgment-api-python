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
    election_id: int,
) -> str:
    if isinstance(vote_ids, int):
        vote_ids = [vote_ids]
    return jws.sign(
        {"votes": vote_ids, "election": election_id},
        settings.secret,
        algorithm="HS256",
    )


def create_admin_token(
    election_id: int,
) -> str:
    return jws.sign(
        {"admin": True, "election": election_id},
        settings.secret,
        algorithm="HS256",
    )
