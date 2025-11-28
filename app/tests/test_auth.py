import pytest
from jose import jws
from ..auth import create_ballot_token, jws_verify, create_admin_token
from ..settings import settings
from .. import errors


def test_jws_verify_dict():
    """
    Can verify a JWS token given as a dict
    """
    payload = {"bar": "foo"}
    token = jws.sign(payload, settings.secret, algorithm="HS256")
    data = jws_verify(token)
    assert payload == data


def test_jws_verify_secret():
    """
    It must fail with a wrong key
    """
    payload = {"bar": "foo"}
    token = jws.sign(payload, settings.secret + "WRONG", algorithm="HS256")
    with pytest.raises(errors.UnauthorizedError):
        jws_verify(token)


def test_jws_verify_bytes():
    """
    It must fail with bytes content
    """
    payload = b"foo"
    token = jws.sign(payload, settings.secret, algorithm="HS256")
    with pytest.raises(errors.BadRequestError):
        jws_verify(token)


def test_ballot_token():
    """
    Can verify ballot tokens with MANY different tokens
    """
    vote_ids = list(range(1000))
    election_ref = "qwertyuiop"
    token = create_ballot_token(vote_ids, election_ref, 1)
    data = jws_verify(token)
    assert data == {"votes": vote_ids, "election": election_ref, "ballot": 1}


def test_admin_token():
    """
    Can verify ballot tokens with MANY different tokens
    """
    election_ref = "qwertyuiop"
    token = create_admin_token(election_ref)
    data = jws_verify(token)
    assert data == {"admin": True, "election": election_ref}
