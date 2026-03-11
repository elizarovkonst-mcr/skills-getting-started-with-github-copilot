from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

# keep a pristine copy of the data so tests can restore state
_original_activities = deepcopy(activities)

@pytest.fixture(autouse=True)
def reset_activities():
    # Arrange: before each test, reset global activities dict
    activities.clear()
    activities.update(deepcopy(_original_activities))


client = TestClient(app)


def test_root_redirect():
    # Arrange is covered by client fixture above
    # Act - do not follow redirects so we can inspect status code
    response = client.get("/", allow_redirects=False)
    # Assert
    assert response.status_code in (307, 302)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities():
    # Act
    response = client.get("/activities")
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    # check a couple of known keys from the original data
    assert "Chess Club" in data
    assert "Gym Class" in data


def test_signup_success():
    email = "newstudent@mergington.edu"
    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})
    # Assert
    assert response.status_code == 200
    body = response.json()
    assert "Signed up" in body.get("message", "")
    assert email in activities["Chess Club"]["participants"]


def test_signup_duplicate():
    existing = _original_activities["Chess Club"]["participants"][0]
    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": existing})
    # Assert
    assert response.status_code == 400


def test_signup_not_found():
    email = "ghost@mergington.edu"
    response = client.post("/activities/Nonexistent/signup", params={"email": email})
    assert response.status_code == 404


def test_unregister_success():
    # Arrange: ensure someone is signed up; use one from original
    email = _original_activities["Gym Class"]["participants"][0]
    # Act
    response = client.post("/activities/Gym Class/unregister", params={"email": email})
    # Assert
    assert response.status_code == 200
    body = response.json()
    assert "Unregistered" in body.get("message", "")
    assert email not in activities["Gym Class"]["participants"]


def test_unregister_not_signed():
    email = "nobody@mergington.edu"
    response = client.post("/activities/Chess Club/unregister", params={"email": email})
    assert response.status_code == 400


def test_unregister_not_found():
    email = "whatever@mergington.edu"
    response = client.post("/activities/Nope/unregister", params={"email": email})
    assert response.status_code == 404
