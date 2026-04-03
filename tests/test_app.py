import pytest
import copy
from fastapi.testclient import TestClient
from src.app import app, activities

# Initial activities data for resetting
initial_activities = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test to prevent state leakage."""
    activities.clear()
    activities.update(copy.deepcopy(initial_activities))


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    return TestClient(app, follow_redirects=False)


def test_root_redirect(client):
    """Test that root endpoint redirects to static index.html."""
    # Arrange
    # Act
    response = client.get("/")
    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities."""
    # Arrange
    # Act
    response = client.get("/activities")
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 9
    assert "Chess Club" in data
    assert "participants" in data["Chess Club"]


def test_signup_success(client):
    """Test successful signup for an activity."""
    # Arrange
    email = "new@student.edu"
    activity_name = "Chess Club"
    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    # Assert
    assert response.status_code == 200
    assert f"Signed up {email} for {activity_name}" in response.json()["message"]
    # Verify participant was added
    response_check = client.get("/activities")
    assert email in response_check.json()[activity_name]["participants"]


def test_signup_duplicate(client):
    """Test signup fails when student is already signed up."""
    # Arrange
    email = "michael@mergington.edu"  # Already in Chess Club
    activity_name = "Chess Club"
    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    # Assert
    assert response.status_code == 400
    assert "Student is already signed up for this activity" in response.json()["detail"]


def test_signup_activity_full(client):
    """Test signup fails when activity is at capacity."""
    # Arrange
    activity_name = "Chess Club"
    activities[activity_name]["participants"] = ["test@test.com"] * 12  # Fill to max
    email = "new@student.edu"
    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    # Assert
    assert response.status_code == 400
    assert "Activity is full" in response.json()["detail"]


def test_signup_invalid_activity(client):
    """Test signup fails for non-existent activity."""
    # Arrange
    email = "test@test.com"
    activity_name = "Invalid Activity"
    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    # Assert
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_remove_participant_success(client):
    """Test successful removal of a participant."""
    # Arrange
    email = "michael@mergington.edu"
    activity_name = "Chess Club"
    # Act
    response = client.delete(f"/activities/{activity_name}/participants?email={email}")
    # Assert
    assert response.status_code == 200
    assert f"Removed {email} from {activity_name}" in response.json()["message"]
    # Verify participant was removed
    response_check = client.get("/activities")
    assert email not in response_check.json()[activity_name]["participants"]


def test_remove_participant_invalid_activity(client):
    """Test removal fails for non-existent activity."""
    # Arrange
    email = "test@test.com"
    activity_name = "Invalid Activity"
    # Act
    response = client.delete(f"/activities/{activity_name}/participants?email={email}")
    # Assert
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_remove_participant_not_found(client):
    """Test removal fails when participant is not in activity."""
    # Arrange
    email = "notfound@test.com"
    activity_name = "Chess Club"
    # Act
    response = client.delete(f"/activities/{activity_name}/participants?email={email}")
    # Assert
    assert response.status_code == 404
    assert "Participant not found" in response.json()["detail"]