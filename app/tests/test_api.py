import string
import itertools
import typing as t
import random
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.auth import jws_verify
from ..database import Base, get_db
from .. import schemas
from ..main import app

test_database_url = "sqlite:///./test.db"
test_engine = create_engine(
    test_database_url, connect_args={"check_same_thread": False}
)
TestingSessionLocal: sessionmaker = sessionmaker(  # type: ignore
    autocommit=False, autoflush=False, bind=test_engine
)

Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_liveness():
    response = client.get("/liveness")
    assert response.status_code == 200, response.status_code
    assert response.text == '"OK"', response.text


def test_read_a_missing_election():
    response = client.get("/elections/foo")
    assert response.status_code == 422


def _random_string(length: int) -> str:
    return "".join(random.choices(string.ascii_letters, k=length))


class RandomElection(t.TypedDict):
    name: str
    candidates: list[dict[str, str]]
    grades: list[dict[str, int | str]]
    restricted: t.NotRequired[bool]
    num_voters: t.NotRequired[int]


def _random_election(num_candidates: int, num_grades: int) -> RandomElection:
    """
    Generate an election with random names
    """
    grades: list[dict[str, int | str]] = [
        {"name": _random_string(10), "value": i} for i in range(num_grades)
    ]
    candidates = [{"name": _random_string(10)} for i in range(num_candidates)]
    name = _random_string(10)
    return {"candidates": candidates, "grades": grades, "name": name}


def test_create_election():
    body = _random_election(2, 2)
    response = client.post("/elections", json=body)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == body["name"]
    assert "id" in data

    assert len(data["candidates"]) == 2
    db_candidate_names = {c["name"] for c in data["candidates"]}
    req_candidate_names = {c["name"] for c in body["candidates"]}
    assert db_candidate_names == req_candidate_names, db_candidate_names

    assert len(data["grades"]) == 2
    db_grade_names = {c["name"] for c in data["grades"]}
    req_grade_names = {c["name"] for c in body["grades"]}
    assert db_grade_names == req_grade_names, db_grade_names


def test_get_election():
    body = _random_election(3, 4)
    response = client.post("/elections", json=body)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == body["name"]
    assert "id" in data

    election_id = data["id"]
    response = client.get(f"/elections/{election_id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == body["name"]
    assert data["id"] == election_id

    assert len(data["candidates"]) == 3
    db_candidate_names = {c["name"] for c in data["candidates"]}
    req_candidate_names = {c["name"] for c in body["candidates"]}
    assert db_candidate_names == req_candidate_names, db_candidate_names

    assert len(data["grades"]) == 4
    db_grade_names = {c["name"] for c in data["grades"]}
    req_grade_names = {c["name"] for c in body["grades"]}
    assert db_grade_names == req_grade_names, db_grade_names


def _generate_votes_from_response(
    mode: t.Literal["id", "name", "value"],
    data: dict[str, t.Any],
):
    if mode == "id":
        candidate_key = "id"
        grade_key = "id"
    else:
        raise NotImplementedError(f"Unknown mode {mode}")

    return [
        {
            "candidate_id": c[candidate_key],
            "grade_id": g[grade_key],
        }
        for c, g in itertools.product(data["candidates"], data["grades"])
    ]


def test_create_vote():
    # Create a random election
    body = _random_election(10, 5)
    response = client.post("/elections", json=body)
    assert response.status_code == 200, response.text
    data = response.json()

    assert "id" in data
    election_id = data["id"]

    # We create votes using the ID
    votes = _generate_votes_from_response("id", data)
    response = client.post(f"/votes", json={"votes": votes, "election_id": election_id})
    assert response.status_code == 200, response.text
    data = response.json()
    for v1, v2 in zip(votes, data["votes"]):
        assert v2["grade"]["id"] == v1["grade_id"]
        assert v2["candidate"]["id"] == v1["candidate_id"]
        assert v2["election_id"] == election_id

    token = data["token"]

    # Now, we check that we need the righ token to read the votes
    response = client.get(f"/votes/{token}WRONG")
    assert response.status_code == 401, response.text

    response = client.get(f"/votes/{token}")
    assert response.status_code == 200, response.text
    data = response.json()
    for v1, v2 in zip(votes, data["votes"]):
        assert v2["grade"]["id"] == v1["grade_id"]
        assert v2["candidate"]["id"] == v1["candidate_id"]
        assert v2["election_id"] == election_id


def test_cannot_create_vote_on_restricted_election():
    """
    On a restricted election, we are not allowed to create new votes
    """
    # Create a random election
    body = _random_election(10, 5)
    body["restricted"] = True
    body["num_voters"] = 1
    response = client.post("/elections", json=body)
    data = response.json()
    assert response.status_code == 200, data
    assert len(data["invites"]) == 1
    election_id = data["id"]

    # We create votes using the ID
    votes = _generate_votes_from_response("id", data)
    response = client.post(f"/votes", json={"votes": votes, "election_id": election_id})
    data = response.json()
    assert response.status_code == 400, data


def test_can_vote_on_restricted_election():
    """
    On a restricted election, we need to update votes.
    """
    # Create a random election
    body = _random_election(10, 5)
    body["restricted"] = True
    body["num_voters"] = 1
    response = client.post("/elections", json=body)
    data = response.json()
    assert response.status_code == 200, data
    tokens = data["invites"]
    assert len(tokens) == 1
    token = tokens[0]

    # Check that the token makes sense
    payload = jws_verify(token)
    assert len(payload["votes"]) == len(data["candidates"])
    assert payload["election"] == data["id"]

    # We create votes using the token
    grade_id = data["grades"][0]["id"]
    votes = [
        {"candidate_id": candidate["id"], "grade_id": grade_id}
        for candidate in data["candidates"]
    ]
    response = client.put(f"/votes", json={"votes": votes, "token": token})
    data = response.json()
    assert response.status_code == 200, data
    assert data["token"] == token


def test_get_results():
    # Create a random election
    body = _random_election(10, 5)
    response = client.post("/elections", json=body)
    assert response.status_code == 200, response.content
    data = response.json()
    election_id = data["id"]

    # We create votes using the ID
    votes = _generate_votes_from_response("id", data)
    # print(data, votes)
    response = client.post(f"/votes", json={"votes": votes, "election_id": election_id})
    data = response.json()
    assert response.status_code == 200, data

    # Now we get the results
    response = client.get(f"/results/{election_id}")
    assert response.status_code == 200, response.text
    data = response.json()
