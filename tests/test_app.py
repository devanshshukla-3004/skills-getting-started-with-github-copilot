import src.app as app_module
from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def client(monkeypatch):
    test_activities = {
        "Chess Club": {
            "description": "Practice chess",
            "schedule": "Fridays",
            "max_participants": 2,
            "participants": ["existing@example.com"],
        },
        "Full Activity": {
            "description": "Already full",
            "schedule": "Mondays",
            "max_participants": 1,
            "participants": ["full@example.com"],
        },
    }
    monkeypatch.setattr(app_module, "activities", test_activities)
    return TestClient(app_module.app)


def test_root_redirects_to_activity_page(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == app_module.activities


def test_signup_adds_participant_to_activity(client):
    email = "new@example.com"

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in client.get("/activities").json()["Chess Club"]["participants"]


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown/signup",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant_without_changing_roster(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "existing@example.com"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert app_module.activities["Chess Club"]["participants"] == ["existing@example.com"]


def test_signup_rejects_full_activity_without_changing_roster(client):
    response = client.post(
        "/activities/Full Activity/signup",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"
    assert app_module.activities["Full Activity"]["participants"] == ["full@example.com"]


def test_unregister_removes_participant_from_activity(client):
    email = "existing@example.com"

    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert email not in client.get("/activities").json()["Chess Club"]["participants"]


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown/signup",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_nonparticipant_without_changing_roster(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "missing@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert app_module.activities["Chess Club"]["participants"] == ["existing@example.com"]