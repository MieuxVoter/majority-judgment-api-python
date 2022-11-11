from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..database import Base
from ..  import schemas
from ..main import app, get_db

test_database_url = "sqlite:///./test.db"
test_engine = create_engine(
    test_database_url, connect_args={"check_same_thread": False}
)
TestingSessionLocal: sessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

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

    # assert response.json() == {
    #     "id": "foo",
    #     "title": "Foo",
    #     "description": "There goes my hero",
    # }
 

def test_create_election():
    grades= [
        dict(name="foo", value=0),
        dict(name="bar", value=1),
        ]
    candidates =  [
        dict(name="foo"),
        dict(name="bar"),
        ]
    body = {"name": "foo", "grades": grades, "candidates": candidates}
    response = client.post(
        "/elections",
        json=body
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "foo"
    assert "id" in data
    election_id = data["id"]

    response = client.get(f"/elections/{election_id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "foo"
    assert data["id"] == election_id
