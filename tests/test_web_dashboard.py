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
