import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def activities():
    return {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 3,
            "participants": ["student@mergington.edu"],
        }
    }


@pytest.fixture
def client(monkeypatch, activities):
    monkeypatch.setattr(app_module, "activities", activities)
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(client, activities):
    # Arrange
    expected_activities = activities

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client, activities):
    # Arrange
    activity_name = "Chess Club"
    email = "new-student@mergington.edu"
    signup_url = f"/activities/{activity_name}/signup"

    # Act
    response = client.post(signup_url, params={"email": email})
    updated_activities = client.get("/activities").json()

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in updated_activities[activity_name]["participants"]
    assert len(updated_activities[activity_name]["participants"]) == 2


def test_signup_returns_404_for_unknown_activity(client):
    # Arrange
    activity_name = "Robotics Club"
    signup_url = f"/activities/{activity_name}/signup"

    # Act
    response = client.post(signup_url, params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_returns_400_for_existing_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "student@mergington.edu"
    signup_url = f"/activities/{activity_name}/signup"

    # Act
    response = client.post(signup_url, params={"email": email})
    current_participants = client.get("/activities").json()[activity_name]["participants"]

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert current_participants.count(email) == 1


def test_unregister_removes_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "student@mergington.edu"
    signup_url = f"/activities/{activity_name}/signup"

    # Act
    response = client.delete(signup_url, params={"email": email})
    updated_activities = client.get("/activities").json()

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in updated_activities[activity_name]["participants"]


def test_unregister_returns_404_for_unknown_activity(client):
    # Arrange
    activity_name = "Robotics Club"
    signup_url = f"/activities/{activity_name}/signup"

    # Act
    response = client.delete(signup_url, params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_404_for_unregistered_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "not-registered@mergington.edu"
    signup_url = f"/activities/{activity_name}/signup"

    # Act
    response = client.delete(signup_url, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not signed up for this activity"