"""Unit tests for Apex Web Dashboard & REST Endpoints."""
import os
import pytest
from fastapi.testclient import TestClient
from apex.gateways.web_dashboard import app


@pytest.fixture
def client():
    return TestClient(app)


def test_serve_dashboard_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "PROJECT APEX" in response.text
    assert "Chat Console" in response.text


def test_api_status(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "active_model" in data
    assert "tools_count" in data
    assert data["tools_count"] > 10
    assert "system" in data


def test_api_tools_list(client):
    response = client.get("/api/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    tool_names = [t["name"] for t in data["tools"]]
    assert "read_document" in tool_names
    assert "query_database" in tool_names
    assert "dispatch_subagents" in tool_names
    assert "synthesize_speech" in tool_names
    assert "scrape_structured_web" in tool_names


def test_api_upload_document(client, tmp_path):
    test_file = tmp_path / "sample.txt"
    test_file.write_text("Baris 1: Test file upload.\nBaris 2: Apex omni-modal parser.")

    with open(test_file, "rb") as f:
        response = client.post("/api/upload", files={"file": ("sample.txt", f, "text/plain")})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "sample.txt" in data["filename"]
    assert "Apex omni-modal parser" in data["parsed_content"]


def test_api_models_list(client):
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert "active_model" in data


def test_api_export_session(client):
    response = client.get("/api/export/test_session_123")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test_session_123"
    assert "Chat Session Export" in data["markdown"]


def test_api_config_get_and_post(client):
    # Test GET /api/config
    get_res = client.get("/api/config")
    assert get_res.status_code == 200
    cfg = get_res.json()
    assert "default_model" in cfg
    assert "active_provider" in cfg

    # Test POST /api/config update
    post_res = client.post("/api/config", json={"key": "routing.budget_mode", "value": "economy"})
    assert post_res.status_code == 200
    assert post_res.json()["success"] is True


def test_api_profiles_and_setup(client):
    # Test GET /api/config/profiles
    p_res = client.get("/api/config/profiles")
    assert p_res.status_code == 200
    p_data = p_res.json()
    assert "profiles" in p_data
    assert "active_profile" in p_data

    # Test POST /api/config/profiles/save
    save_res = client.post("/api/config/profiles/save", json={"name": "web_test_prof"})
    assert save_res.status_code == 200
    assert save_res.json()["success"] is True

    # Test POST /api/config/profiles/use
    use_res = client.post("/api/config/profiles/use", json={"name": "web_test_prof"})
    assert use_res.status_code == 200
    assert use_res.json()["success"] is True

    # Switch back to default
    client.post("/api/config/profiles/use", json={"name": "default"})
    from apex.config import config
    config.delete_profile("web_test_prof")

    # Test GET /api/setup/check
    check_res = client.get("/api/setup/check")
    assert check_res.status_code == 200
    assert "checks" in check_res.json()

    # Test POST /api/setup/repair
    repair_res = client.post("/api/setup/repair")
    assert repair_res.status_code == 200
    assert repair_res.json()["success"] is True

    # Test POST /api/config/sync-env
    sync_res = client.post("/api/config/sync-env")
    assert sync_res.status_code == 200
    assert "updated" in sync_res.json()


