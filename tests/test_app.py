import copy
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import app as app_module  # noqa: E402


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset in-memory activities after each test to avoid state bleed."""
    snapshot = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(snapshot))


@pytest.fixture()
def client():
    return TestClient(app_module.app)


def test_root_redirects_to_static(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (307, 308)
    assert response.headers["location"].endswith("/static/index.html")


def test_get_activities_returns_seed_data(client):
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()

    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_adds_participant_and_prevents_duplicates(client):
    email = "newstudent@mergington.edu"
    activity = "Chess Club"

    first_response = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert first_response.status_code == 200
    assert email in app_module.activities[activity]["participants"]

    second_response = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert second_response.status_code == 400


def test_delete_participant_removes_from_activity(client):
    activity = "Gym Class"
    email = "john@mergington.edu"

    response = client.delete(f"/activities/{activity}/participants", params={"email": email})
    assert response.status_code == 200
    assert email not in app_module.activities[activity]["participants"]

    # Removing again should yield not found
    repeat_response = client.delete(f"/activities/{activity}/participants", params={"email": email})
    assert repeat_response.status_code == 404
