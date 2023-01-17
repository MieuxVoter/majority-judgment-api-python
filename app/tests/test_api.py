import string
import copy
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
    test_database_url, connect_args={"check_same_thread": False}, echo=True
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
    assert response.status_code == 404


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
    assert "ref" in data

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
    assert "ref" in data

    election_ref = data["ref"]
    response = client.get(f"/elections/{election_ref}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == body["name"]
    assert data["ref"] == election_ref

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
            "grade_id": random.choice(data["grades"])[grade_key],
        }
        for c in data["candidates"]
    ]


def test_create_ballot():
    # Create a random election
    body = _random_election(10, 5)
    response = client.post("/elections", json=body)
    assert response.status_code == 200, response.text
    data = response.json()

    assert "ref" in data
    election_ref = data["ref"]

    # We create many votes using the election ID
    votes = _generate_votes_from_response("id", data)
    response = client.post(
        f"/ballots", json={"votes": votes, "election_ref": election_ref}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    for v1, v2 in zip(votes, data["votes"]):
        assert v2["grade"]["id"] == v1["grade_id"]
        assert v2["candidate"]["id"] == v1["candidate_id"]
        assert v2["election_ref"] == election_ref

    token = data["token"]

    # Now, we check that we need the right token to read the votes
    response = client.get(
        f"/ballots/", headers={"Authorization": f"Bearer {token}WRONG"}
    )
    assert response.status_code == 401, response.text

    response = client.get(f"/ballots/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.text
    data = response.json()
    for v1, v2 in zip(votes, data["votes"]):
        assert v2["grade"]["id"] == v1["grade_id"]
        assert v2["candidate"]["id"] == v1["candidate_id"]
        assert v2["election_ref"] == election_ref


def test_reject_incomplete_ballots():
    """
    This tests that a ballot contains a many vote as the number of candidates in an election
    """
    # Create a random election
    body = _random_election(10, 5)
    response = client.post("/elections", json=body)
    assert response.status_code == 200, response.text
    data = response.json()

    # Create a ballot with one vote less than the number of candidates
    votes = _generate_votes_from_response("id", data)
    response = client.post(
        f"/ballots", json={"votes": votes[:-1], "election_ref": data["ref"]}
    )
    assert response.status_code == 403, response.text

    # But it should work with the whole ballot
    votes = _generate_votes_from_response("id", data)
    response = client.post(
        f"/ballots", json={"votes": votes, "election_ref": data["ref"]}
    )
    assert response.status_code == 200, response.text


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
    election_ref = data["ref"]

    # We create votes using the ID
    votes = _generate_votes_from_response("id", data)
    response = client.post(
        f"/ballots",
        json={"votes": votes, "election_ref": election_ref},
    )
    data = response.json()
    assert response.status_code == 403, data


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
    assert payload["election"] == data["ref"]

    # We create votes using the token
    grade_id = data["grades"][0]["id"]
    votes = [
        {"candidate_id": candidate["id"], "grade_id": grade_id}
        for candidate in data["candidates"]
    ]
    response = client.put(
        f"/ballots",
        json={"votes": votes},
        headers={"Authorization": f"Bearer {token}"},
    )
    data = response.json()
    assert response.status_code == 200, data

    payload2 = jws_verify(data["token"])
    assert payload2 == payload


def test_cannot_ballot_box_stuffing():
    # Create a random election
    body = _random_election(10, 5)
    response = client.post("/elections", json=body)
    assert response.status_code == 200, response.content
    data = response.json()
    election_ref = data["ref"]

    # We create votes using the ID
    votes = _generate_votes_from_response("id", data)
    assert len(votes) == len(data["candidates"])
    response = client.post(
        f"/ballots", json={"votes": votes + votes, "election_ref": election_ref}
    )
    data = response.json()
    assert response.status_code == 403, data


def test_get_results():
    # Create a random election
    body = _random_election(10, 5)
    response = client.post("/elections", json=body)
    assert response.status_code == 200, response.content
    data = response.json()
    election_ref = data["ref"]

    # We create votes using the ID
    votes = _generate_votes_from_response("id", data)
    response = client.post(
        f"/ballots", json={"votes": votes, "election_ref": election_ref}
    )
    data = response.json()
    assert response.status_code == 200, data

    # Now we get the results
    response = client.get(f"/results/{election_ref}")
    assert response.status_code == 200, response.text
    data = response.json()
    profile = data["merit_profile"]

    assert len(profile) == len(data["candidates"])


def test_update_election():
    # Create a random election
    body = _random_election(10, 5)
    response = client.post("/elections", json=body)
    assert response.status_code == 200, response.content
    data = response.json()
    new_name = f'{data["name"]}_MODIFIED'
    data["name"] = new_name
    token = data["admin"]

    # Check we can not update without the token
    response = client.put("/elections", json=data)
    assert response.status_code == 422, response.content

    # Check that the request fails with a wrong token
    response = client.put(
        f"/elections", json=data, headers={"Authorization": f"Bearer {token}WRONG"}
    )
    assert response.status_code == 401, response.text

    # But it works with the right token
    response = client.put(
        f"/elections", json=data, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.text
    response2 = client.get(f"/elections/{data['ref']}", json=data)
    assert response2.status_code == 200, response2.text
    data2 = response2.json()
    assert data2["name"] == new_name

    # We can update a candidate, or a grade
    data["candidates"][0]["name"] += "MODIFIED"
    data["candidates"][0]["description"] += "MODIFIED"
    data["candidates"][0]["image"] += "MODIFIED"
    data["grades"][0]["name"] += "MODIFIED"
    data["grades"][0]["description"] += "MODIFIED"
    data["grades"][0]["value"] += 10
    response = client.put(
        f"/elections", json=data, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["candidates"][0]["name"].endswith("MODIFIED")
    assert data["grades"][0]["name"].endswith("MODIFIED")

    # But, we can not change the candidate IDs
    data2 = copy.deepcopy(data)
    del data2["candidates"][-1]
    response = client.put(
        f"/elections", json=data2, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403, response.text

    data2 = copy.deepcopy(data)
    data2["grades"][0]["id"] += 100
    response = client.put(
        f"/elections", json=data2, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403, response.text


def test_close_election():
    # Create a random election
    body = _random_election(10, 5)
    response = client.post("/elections", json=body)
    assert response.status_code == 200, response.content
    data = response.json()
    assert data["force_close"] == False
    data["force_close"] = True
    token = data["admin"]

    # Check that the request fails with a wrong token
    response = client.put(
        f"/elections", json=data, headers={"Authorization": f"Bearer {token}WRONG"}
    )
    assert response.status_code == 401, response.text

    # But it works with the right token
    print("UPDATE", data["force_close"])
    response = client.put(
        f"/elections", json=data, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.text
    response2 = client.get(f"/elections/{data['ref']}", json=data)
    assert response2.status_code == 200, response2.text
    data2 = response2.json()
    assert data2["force_close"] == True
