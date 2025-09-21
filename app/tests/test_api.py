import string
import copy
from datetime import datetime, timedelta
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
    test_database_url, connect_args={"check_same_thread": False}, echo=False
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


def check_error_response(response, expected_status_code: int, expected_error_code: str):
    """
    Helper function to assert a standardized error response from the API.
    It checks the status code and the specific error code in the JSON body.
    """
    assert response.status_code == expected_status_code, \
        f"Expected status {expected_status_code}, but got {response.status_code}. Body: {response.text}"

    data = response.json()

    assert "error" in data, f"Key 'error' not found in response body: {data}"
    assert data["error"] == expected_error_code, \
        f"Expected error code '{expected_error_code}', but got '{data['error']}'"

    return data  # Return the parsed data in case a test needs to check the message


def test_liveness():
    response = client.get("/liveness")
    assert response.status_code == 200, response.status_code
    assert response.text == '"OK"', response.text


def test_read_a_missing_election():
    response = client.get("/elections/foo")
    check_error_response(response, 404, "NOT_FOUND")


def _random_string(length: int) -> str:
    return "".join(random.choices(string.ascii_letters, k=length))


class RandomElection(t.TypedDict):
    name: str
    candidates: list[dict[str, str]]
    grades: list[dict[str, int | str]]
    restricted: bool
    hide_results: bool
    num_voters: int
    date_end: t.Optional[str]
    date_start: t.Optional[str]
    auth_for_result: bool


def _random_election(num_candidates: int, num_grades: int) -> RandomElection:
    """
    Generate an election with random names
    """
    grades: list[dict[str, int | str]] = [
        {"name": _random_string(10), "value": i} for i in range(num_grades)
    ]
    candidates = [{"name": _random_string(10)} for i in range(num_candidates)]
    name = _random_string(10)
    return {
        "date_start":None,
        "candidates": candidates, 
        "grades": grades, 
        "name": name,
        "restricted": False,
        "hide_results": False,
        "num_voters": 0,
        "date_end": None,
        "auth_for_result": False,
    }


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

    # Can create an election with a null date_end
    body = _random_election(2, 2)
    body["date_end"] = None
    response = client.post("/elections", json=body)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == body["name"]


def test_start_end_date_are_valid():
    # cannot create an election where the start date is after the end date 
    body = _random_election(2, 2)
    body["date_start"] = (datetime.now() + timedelta(days=1)).isoformat()
    body["date_end"] = (datetime.now()).isoformat()
    response = client.post("/elections", json=body)
    check_error_response(response, 422, "SCHEMA_VALIDATION_ERROR")

    body["date_start"] = (datetime.now()).isoformat()
    body["date_end"] = (datetime.now() + timedelta(days=1)).isoformat()
    response = client.post("/elections", json=body)
    assert response.status_code == 200, response.text
    election_data = response.json()
    del election_data["candidates"]
    del election_data["grades"]
    del election_data["name"]
    del election_data["restricted"]
    del election_data["hide_results"]
    del election_data["auth_for_result"]
    admin_token = election_data["admin"]
    election_ref = election_data["ref"]

    # update election should not be allowed if the new start date is after the new end date
    election_data["date_start"] = (datetime.now() + timedelta(days=1)).isoformat()
    election_data["date_end"] = (datetime.now()).isoformat()
    response = client.put("/elections", json=election_data, headers={"Authorization": f"Bearer {admin_token}"})
    check_error_response(response, 422, "SCHEMA_VALIDATION_ERROR")

    # update election should be rejected if the new end date is before the existing start date
    del election_data["date_start"]
    election_data["date_end"] = (datetime.now() - timedelta(days=1)).isoformat()
    response = client.put("/elections", json=election_data, headers={"Authorization": f"Bearer {admin_token}"})
    check_error_response(response, 409, "INVALID_DATE_CONFIGURATION")

    # update election should be rejected if the new start date is after the existing end date
    del election_data["date_end"]
    election_data["date_start"] = (datetime.now() + timedelta(days=2)).isoformat()
    response = client.put("/elections", json=election_data, headers={"Authorization": f"Bearer {admin_token}"})
    check_error_response(response, 409, "INVALID_DATE_CONFIGURATION")

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

    ballot_token = data["token"]

    # Now, we check that we need the right ballot_token to read the votes
    response = client.get(
        f"/ballots/", headers={"Authorization": f"Bearer {ballot_token}WRONG"}
    )
    check_error_response(response, 401, "UNAUTHORIZED")

    response = client.get(f"/ballots/", headers={"Authorization": f"Bearer {ballot_token}"})
    assert response.status_code == 200, response.text
    data = response.json()
    for v1, v2 in zip(votes, data["votes"]):
        assert v2["grade"]["id"] == v1["grade_id"]
        assert v2["candidate"]["id"] == v1["candidate_id"]
        assert v2["election_ref"] == election_ref


def test_reject_wrong_ballots_restricted_election():
    """
    This tests that a  ballot contains a many vote as the number of candidates in an election.
    Here we consider a restricted election.
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
    ballot_token = tokens[0]
    grade_id = data["grades"][0]["id"]
    votes = [
        {"candidate_id": candidate["id"], "grade_id": grade_id}
        for candidate in data["candidates"]
    ]

    # Check a ballot with one vote less than the number of candidates is rejected
    response = client.put(
        f"/ballots",
        json={"votes": votes[-1]},
        headers={"Authorization": f"Bearer {ballot_token}"},
    )
    check_error_response(response, 422, "VALIDATION_ERROR")

    # Check that a ballot with an empty grade_id is rejected
    grade_id = data["grades"][0]["id"]
    votes2 = copy.deepcopy(votes)
    votes2[0]["grade_id"] = None
    response = client.put(
        f"/ballots",
        json={"votes": votes2},
        headers={"Authorization": f"Bearer {ballot_token}"},
    )
    check_error_response(response, 422, "VALIDATION_ERROR")

    # Check that a ballot with an empty candidate is rejected
    votes2 = copy.deepcopy(votes)
    votes2[0]["candidate_id"] = None
    response = client.put(
        f"/ballots",
        json={"votes": votes2},
        headers={"Authorization": f"Bearer {ballot_token}"},
    )
    check_error_response(response, 422, "VALIDATION_ERROR")

    # But it should work with the whole ballot
    response = client.put(
        f"/ballots",
        json={"votes": votes},
        headers={"Authorization": f"Bearer {ballot_token}"},
    )
    assert response.status_code == 200, response.json()

    # Check that we can now get this ballot
    response = client.get(
        f"/ballots",
        headers={"Authorization": f"Bearer {ballot_token}"},
    )
    assert response.status_code == 200, response.json()

def test_rejects_update_with_empty_ballot():
    """
    Tests that updating a ballot with an empty list of votes is rejected.
    """
    # Create a restricted election to get a valid ballot token
    body = _random_election(5, 3)
    body["restricted"] = True
    body["num_voters"] = 1
    response = client.post("/elections", json=body)
    assert response.status_code == 200
    election_data = response.json()
    ballot_token = election_data["invites"][0]

    # Attempt to update the ballot with an empty votes array
    response = client.put(
        "/ballots",
        json={"votes": []},
        headers={"Authorization": f"Bearer {ballot_token}"},
    )
    check_error_response(response, 400, "BAD_REQUEST")

def test_reject_wrong_ballots_unrestricted_election():
    """
    This tests that a  ballot contains a many vote as the number of candidates in an election
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
    check_error_response(response, 403, "INCONSISTENT_BALLOT")

    # Check that a ballot with an empty grade_id is rejected
    votes = _generate_votes_from_response("id", data)
    votes[0]["grade_id"] = None
    response = client.post(
        f"/ballots", json={"votes": votes, "election_ref": data["ref"]}
    )
    check_error_response(response, 422, "VALIDATION_ERROR")

    # Check that a ballot with an empty candidate is rejected
    votes = _generate_votes_from_response("id", data)
    votes[0]["candidate_id"] = None
    response = client.post(
        f"/ballots", json={"votes": votes, "election_ref": data["ref"]}
    )
    check_error_response(response, 422, "VALIDATION_ERROR")

    # But it should work with the whole ballot
    votes = _generate_votes_from_response("id", data)
    response = client.post(
        f"/ballots", json={"votes": votes, "election_ref": data["ref"]}
    )
    assert response.status_code == 200, response.text


def test_cannot_create_vote_on_ended_election():
    """
    On an ended election, we are not allowed to create new votes
    """
    # Create a random election
    body = _random_election(10, 5)
    body["date_start"] = (datetime.now() - timedelta(days=2)).isoformat()
    body["date_end"] = (datetime.now() - timedelta(days=1)).isoformat()
    response = client.post("/elections", json=body)
    election_data = response.json()
    assert response.status_code == 200, election_data
    assert len(election_data["invites"]) == 0
    election_ref = election_data["ref"]
    admin_token = election_data["admin"]

    # We create votes using the ID
    votes = _generate_votes_from_response("id", election_data)
    response = client.post(
        f"/ballots",
        json={"votes": votes, "election_ref": election_ref},
    )
    check_error_response(response, 403, "ELECTION_FINISHED")

    # Try to close the election with force_close
    response = client.put(
        f"/elections",
        json={"force_close": True, "date_end":(datetime.now() + timedelta(days=1)).isoformat(), "ref": election_ref},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.json()

    votes = _generate_votes_from_response("id", election_data)
    response = client.post(
        f"/ballots",
        json={"votes": votes, "election_ref": election_ref},
    )
    check_error_response(response, 403, "ELECTION_FINISHED")

def test_cannot_update_vote_on_ended_election():
    """
    On an ended restricted election, we are not allowed to update votes
    """
    """
    This tests that a  ballot contains a many vote as the number of candidates in an election.
    Here we consider a restricted election.
    """
    # Create a random election
    body = _random_election(10, 5)
    body["restricted"] = True
    body["num_voters"] = 1
    response = client.post("/elections", json=body)
    election_data = response.json()
    election_ref = election_data["ref"]
    election_token = election_data["admin"]
    assert response.status_code == 200, election_data
    tokens = election_data["invites"]
    assert len(tokens) == 1

    # Test for force_close = True
    response = client.put(
        f"/elections",
        json={"force_close": True, "date_end":(datetime.now() + timedelta(days=1)).isoformat(), "ref": election_ref},
        headers={"Authorization": f"Bearer {election_token}"},
    )

    ballot_token = tokens[0]
    grade_id = election_data["grades"][0]["id"]
    votes = [
        {"candidate_id": candidate["id"], "grade_id": grade_id}
        for candidate in election_data["candidates"]
    ]

    response = client.put(
        f"/ballots",
        json={"votes": votes},
        headers={"Authorization": f"Bearer {ballot_token}"},
    )
    check_error_response(response, 403, "ELECTION_FINISHED")

    # Test for date_end in the past
    response = client.put(
        f"/elections",
        json={"force_close": False, "date_start":(datetime.now() - timedelta(days=2)).isoformat(), "date_end":(datetime.now() - timedelta(days=1)).isoformat(), "ref": election_ref},
        headers={"Authorization": f"Bearer {election_token}"},
    )

    assert response.status_code == 200, response.json()["date_end"]

    print(response.json()["date_end"])

    response = client.put(
        f"/ballots",
        json={"votes": votes},
        headers={"Authorization": f"Bearer {ballot_token}"},
    )
    check_error_response(response, 403, "ELECTION_FINISHED")

def test_cannot_change_start_date_if_vote_is_cast():
    """
    Tests that the start_date of an election cannot be updated
    once at least one vote has been cast.
    """
    # Create a restricted election that is already open
    body = _random_election(5, 3)
    body["restricted"] = True
    body["num_voters"] = 1
    body["date_start"] = (datetime.now() - timedelta(days=1)).isoformat()
    body["date_end"] = (datetime.now() + timedelta(days=1)).isoformat()

    response = client.post("/elections", json=body)
    assert response.status_code == 200
    election_data = response.json()
    election_ref = election_data["ref"]
    admin_token = election_data["admin"]
    ballot_token = election_data["invites"][0]

    # Cast a vote to make the election "active"
    grade_id = election_data["grades"][0]["id"]
    votes = [
        {"candidate_id": c["id"], "grade_id": grade_id}
        for c in election_data["candidates"]
    ]
    response = client.put(
        "/ballots",
        json={"votes": votes},
        headers={"Authorization": f"Bearer {ballot_token}"}
    )
    assert response.status_code == 200, "Setup failed: Could not cast the initial vote."

    # Attempt to change the start_date, which should be forbidden
    update_payload = {"ref": election_ref, "date_start": (datetime.now() - timedelta(days=2)).isoformat()}
    response = client.put("/elections", json=update_payload, headers={"Authorization": f"Bearer {admin_token}"})
    check_error_response(response, 403, "ELECTION_IS_ACTIVE")

def test_cannot_create_vote_on_unstarted_election():
    """
    On an unstarted election, we are not allowed to create new votes
    """
    # Create a random election
    body = _random_election(10, 5)
    body["date_start"] = (datetime.now() + timedelta(days=1)).isoformat()
    body["date_end"] = (datetime.now() + timedelta(days=2)).isoformat()
    response = client.post("/elections", json=body)
    data = response.json()
    assert response.status_code == 200, data
    election_ref = data["ref"]

    # We create votes using the ID
    votes = _generate_votes_from_response("id", data)
    response = client.post(
        f"/ballots",
        json={"votes": votes, "election_ref": election_ref},
    )
    check_error_response(response, 403, "ELECTION_NOT_STARTED")

def test_cannot_update_vote_on_unstarted_election():
    """
    On an unstarted election, we are not allowed to create new votes
    """
    # Create a random election
    body = _random_election(10, 5)
    body["restricted"] = True
    body["num_voters"] = 1
    body["date_start"] = (datetime.now() + timedelta(days=1)).isoformat()
    body["date_end"] = (datetime.now() + timedelta(days=2)).isoformat()
    response = client.post("/elections", json=body)
    data = response.json()
    assert response.status_code == 200, data
    election_ref = data["ref"]
    tokens = data["invites"]
    assert len(tokens) == 1

    # We create votes using the ID
    votes = _generate_votes_from_response("id", data)
    response = client.put(
        f"/ballots",
        json={"votes": votes, "election_ref": election_ref},
        headers={"Authorization": f"Bearer {tokens[0]}"},
    )
    check_error_response(response, 403, "ELECTION_NOT_STARTED")

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
    check_error_response(response, 403, "ELECTION_RESTRICTED")

def test_can_vote_on_restricted_election():
    """
    On a restricted election, we can update votes.
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
    ballot_token = tokens[0]

    # Check that the ballot_token makes sense
    payload = jws_verify(ballot_token)
    assert len(payload["votes"]) == len(data["candidates"])
    assert payload["election"] == data["ref"]

    # We create votes using the ballot_token
    grade_id = data["grades"][0]["id"]
    votes = [
        {"candidate_id": candidate["id"], "grade_id": grade_id}
        for candidate in data["candidates"]
    ]
    response = client.put(
        f"/ballots",
        json={"votes": votes},
        headers={"Authorization": f"Bearer {ballot_token}"},
    )
    data = response.json()
    assert response.status_code == 200, data

    payload2 = jws_verify(data["token"])
    assert payload2 == payload


def test_reject_ballot_box_stuffing():
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
    check_error_response(response, 403, "INCONSISTENT_BALLOT")

def test_get_results_for_election_with_no_votes():
    """
    Tests that requesting results for an election with zero votes
    returns the correct specific error.
    """
    # Create a new, open election. Do not cast any votes.
    body = _random_election(10, 5)
    # Ensure the election is considered "closed" so we don't get a RESULTS_HIDDEN error
    body["date_start"] = (datetime.now() - timedelta(days=2)).isoformat()
    body["date_end"] = (datetime.now() - timedelta(days=1)).isoformat()
    response = client.post("/elections", json=body)
    assert response.status_code == 200
    election_ref = response.json()["ref"]

    # Request the results, which should fail predictably.
    response = client.get(f"/results/{election_ref}")
    check_error_response(response, 403, "NO_RECORDED_VOTES")

def test_get_results():
    # Create a random election
    body = _random_election(10, 5)
    body["hide_results"] = False
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


def test_get_results_with_hidden_results():
    # Create a random election
    body = _random_election(10, 5)
    body["hide_results"] = True
    body["date_end"] = (datetime.now() + timedelta(days=1)).isoformat()
    response = client.post("/elections", json=body)
    assert response.status_code == 200, response.content
    data = response.json()
    election_ref = data["ref"]
    admin_token = data["admin"]

    # We create votes using the ID
    votes = _generate_votes_from_response("id", data)
    response = client.post(
        f"/ballots", json={"votes": votes, "election_ref": election_ref}
    )
    assert response.status_code == 200, data

    # But, we can't get the results
    response = client.get(f"/results/{election_ref}")
    check_error_response(response, 403, "RESULTS_HIDDEN")

    # So, we close the election
    update_payload = {
        "ref": election_ref,
        "force_close": True
    }
    response = client.put(
        f"/elections", json=update_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()

    # Now, we can access to the results
    response = client.get(f"/results/{election_ref}")
    assert response.status_code == 200, response.text


def test_get_results_with_auth_for_result():
    # Create a random election
    body = _random_election(10, 5)
    body["auth_for_result"] = True
    body["date_end"] = (datetime.now() + timedelta(days=1)).isoformat()
    response = client.post("/elections", json=body)
    assert response.status_code == 200, response.content
    data = response.json()
    election_ref = data["ref"]
    admin_token = data["admin"]

    # We create votes using the ID
    votes = _generate_votes_from_response("id", data)
    response = client.post(
        f"/ballots", json={"votes": votes, "election_ref": election_ref}
    )
    assert response.status_code == 200, data

    # Send a minimal update to ensure the election state is processed without triggering date change errors.
    update_payload = {"ref": election_ref, "name": data["name"]}
    response = client.put(
        f"/elections", json=update_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200, response.text

    # But, we can't get the results
    response = client.get(f"/results/{election_ref}")
    check_error_response(response, 401, "UNAUTHORIZED")

    # Now, we can access to the results
    response = client.get(f"/results/{election_ref}", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200, response.text

    # Ensure other admin tokens can't access the results
    response = client.post("/elections", json=body)
    assert response.status_code == 200, response.content
    data2 = response.json()
    admin_token2 = data2["admin"]

    response = client.get(f"/results/{election_ref}", headers={"Authorization": f"Bearer {admin_token2}"})
    check_error_response(response, 401, "UNAUTHORIZED")

def test_update_election():
    # Create a random election
    body = _random_election(10, 5)
    response = client.post("/elections", json=body)
    assert response.status_code == 200, response.content
    data = response.json()
    new_name = f'{data["name"]}_MODIFIED'
    data["name"] = new_name
    admin_token = data["admin"]

    # Check we can not update without the ballot_token
    response = client.put("/elections", json=data)
    check_error_response(response, 422, "VALIDATION_ERROR")

    # Check that the request fails with a wrong ballot_token
    response = client.put(
        f"/elections", json=data, headers={"Authorization": f"Bearer {admin_token}WRONG"}
    )
    check_error_response(response, 401, "UNAUTHORIZED")

    # Check that the request fails with a admnin token of other election
    response2 = client.post("/elections", json=body)
    data2 = response2.json()
    admin_token2 = data2["admin"]
    response = client.put(
        f"/elections", json=data, headers={"Authorization": f"Bearer {admin_token2}"}
    )
    check_error_response(response, 403, "WRONG_ELECTION")

    # But it works with the right ballot_token
    response = client.put(
        f"/elections", json=data, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200, response.text
    response2 = client.get(f"/elections/{data['ref']}")
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
        f"/elections", json=data, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["candidates"][0]["name"].endswith("MODIFIED")
    assert data["grades"][0]["name"].endswith("MODIFIED")

    # But, we can not change the candidate IDs
    data2 = copy.deepcopy(data)
    del data2["candidates"][-1]
    response = client.put(
        f"/elections", json=data2, headers={"Authorization": f"Bearer {admin_token}"}
    )
    check_error_response(response, 403, "IMMUTABLE_IDS")

    data2 = copy.deepcopy(data)
    data2["grades"][0]["id"] += 100
    response = client.put(
        f"/elections", json=data2, headers={"Authorization": f"Bearer {admin_token}"}
    )
    check_error_response(response, 403, "IMMUTABLE_IDS")

def test_update_election_as_non_admin():
    """
    Tests that a non-admin user cannot update an election.
    """
    # Create a restricted election to get both an admin and a non-admin (ballot) token.
    body = _random_election(5, 3)
    body["restricted"] = True
    body["num_voters"] = 1
    response = client.post("/elections", json=body)
    assert response.status_code == 200
    election_data = response.json()
    ballot_token = election_data["invites"][0] # This is a non-admin token

    # Attempt to update the election using the ballot token.
    update_payload = {"ref": election_data["ref"], "name": "New Name"}
    response = client.put("/elections", json=update_payload, headers={"Authorization": f"Bearer {ballot_token}"})
    check_error_response(response, 403, "FORBIDDEN")

def test_close_election2():
    """
    Test we can partially update an election
    """
    # Create a random election
    body = _random_election(10, 5)
    response = client.post("/elections", json=body)
    assert response.status_code == 200, response.content
    data = response.json()
    new_name = f'{data["name"]}_MODIFIED'
    data["name"] = new_name
    ballot_token = data["admin"]
    election_ref = data["ref"]

    close_response = client.put(
        f"/elections",
        headers={"Authorization": f"Bearer {ballot_token}"},
        json={"force_close": True, "ref": election_ref},
    )
    assert close_response.status_code == 200, close_response.json()
    close_data = close_response.json()
    assert close_data["force_close"] == True


def test_close_election():
    # Create a random election
    body = _random_election(10, 5)
    response = client.post("/elections", json=body)
    assert response.status_code == 200, response.content
    data = response.json()
    ballot_token = data["admin"]

    # Check that the request fails with a wrong ballot_token
    data["force_close"] = True
    response = client.put(
        f"/elections", json=data, headers={"Authorization": f"Bearer {ballot_token}WRONG"}
    )
    check_error_response(response, 401, "UNAUTHORIZED")

    # But it works with the right ballot_token
    response = client.put(
        f"/elections", json=data, headers={"Authorization": f"Bearer {ballot_token}"}
    )
    assert response.status_code == 200, response.text
    response2 = client.get(f"/elections/{data['ref']}")
    assert response2.status_code == 200, response2.text
    data2 = response2.json()
    assert data2["force_close"] == True


def test_progress():
    # Create a random election using invitations
    body = _random_election(10, 5)
    body["restricted"] = True
    body["num_voters"] = 10
    response = client.post("/elections", json=body)
    data = response.json()
    election_ref = data["ref"]
    assert response.status_code == 200, data

    # Get the progress and check that none of the voters have already voted
    admin = data["admin"]
    progress_rep = client.get(
        f"/elections/{data['ref']}/progress",
        headers={"Authorization": f"Bearer {admin}"},
    )
    progress_data = progress_rep.json()
    assert progress_rep.status_code == 200, progress_data
    assert progress_data["num_voters"] == 10
    assert progress_data["num_voters_voted"] == 0

    # Vote with the first voter
    ballot_token = data["invites"][0]
    grade_id = data["grades"][0]["id"]
    votes = [
        {"candidate_id": candidate["id"], "grade_id": grade_id}
        for candidate in data["candidates"]
    ]
    vote_rep = client.put(
        f"/ballots",
        headers={"Authorization": f"Bearer {ballot_token}"},
        json={"votes": votes},
    )
    vote_data = vote_rep.json()
    assert vote_rep.status_code == 200, vote_data

    # Check the progress has changed
    progress_rep = client.get(
        f"/elections/{data['ref']}/progress",
        headers={"Authorization": f"Bearer {admin}"},
    )
    progress_data = progress_rep.json()
    assert progress_rep.status_code == 200, progress_data
    assert progress_data["num_voters"] == 10
    assert progress_data["num_voters_voted"] == 1
