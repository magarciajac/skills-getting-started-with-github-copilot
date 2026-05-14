"""
Tests for the Mergington High School API
Using the AAA (Arrange-Act-Assert) pattern with pytest and FastAPI TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to original state before each test."""
    original = {
        key: {**value, "participants": list(value["participants"])}
        for key, value in activities.items()
    }
    yield
    for key in activities:
        if key in original:
            activities[key]["participants"] = original[key]["participants"]


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


# --- GET / ---

class TestRoot:
    def test_root_redirects_to_index(self, client):
        # Arrange & Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


# --- GET /activities ---

class TestGetActivities:
    def test_get_activities_returns_all(self, client):
        # Arrange & Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_activity_has_expected_fields(self, client):
        # Arrange & Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


# --- POST /activities/{activity_name}/signup ---

class TestSignup:
    def test_signup_success(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"

    def test_signup_adds_participant(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        client.post(f"/activities/{activity_name}/signup?email={email}")
        response = client.get("/activities")

        # Assert
        assert email in response.json()[activity_name]["participants"]

    def test_signup_nonexistent_activity(self, client):
        # Arrange
        email = "student@mergington.edu"

        # Act
        response = client.post(
            "/activities/NonexistentActivity/signup?email=" + email
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_registration(self, client):
        # Arrange - use an email already in the participants list
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is already signed up"


# --- DELETE /activities/{activity_name}/signup ---

class TestUnregister:
    def test_unregister_success(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"

    def test_unregister_removes_participant(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        client.delete(f"/activities/{activity_name}/signup?email={email}")
        response = client.get("/activities")

        # Assert
        assert email not in response.json()[activity_name]["participants"]

    def test_unregister_nonexistent_activity(self, client):
        # Arrange & Act
        response = client.delete(
            "/activities/NonexistentActivity/signup?email=student@mergington.edu"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_signed_up(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "nobody@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not signed up"
