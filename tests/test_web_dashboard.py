"""Unit tests for Apex Web Dashboard & REST Endpoints."""
import json
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


def test_api_keys_crud(client):
    """Test full CRUD operations for 9Router-compatible API keys."""
    # 1. GET /api/keys
    res = client.get("/api/keys")
    assert res.status_code == 200
    data = res.json()
    assert "keys" in data
    assert isinstance(data["keys"], list)

    # 2. POST /api/keys (Create new key)
    create_res = client.post("/api/keys", json={"name": "test_team_key", "quota": "100000 / 24h"})
    assert create_res.status_code == 200
    create_data = create_res.json()
    assert create_data["success"] is True
    created_key = create_data["key"]
    assert created_key["name"] == "test_team_key"
    assert created_key["key"].startswith("sk-9r-")
    assert len(created_key["key"]) > 30
    assert created_key["quota"] == "100000 / 24h"
    assert created_key["is_active"] is True
    key_id = created_key["id"]

    # 3. PUT /api/keys/{id} (Pause/Deactivate key)
    toggle_res = client.put(f"/api/keys/{key_id}", json={"is_active": False})
    assert toggle_res.status_code == 200
    assert toggle_res.json()["success"] is True
    assert toggle_res.json()["key"]["is_active"] is False

    # 4. DELETE /api/keys/{id}
    del_res = client.delete(f"/api/keys/{key_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Verify key is removed
    res_after = client.get("/api/keys")
    key_ids = [k["id"] for k in res_after.json()["keys"]]
    assert key_id not in key_ids


def test_v1_models_and_proxy_auth(client):
    """Test /v1/models and API key authentication on /v1 endpoints."""
    # 1. /v1/models
    res = client.get("/v1/models")
    assert res.status_code == 200
    data = res.json()
    assert data["object"] == "list"
    assert len(data["data"]) > 0
    model_ids = [m["id"] for m in data["data"]]
    assert "gpt-4o" in model_ids

    # 2. /v1/chat/completions without key -> 401
    unauth_res = client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "hi"}]})
    assert unauth_res.status_code == 401

    # 3. Create a valid key and test authenticated call
    key_res = client.post("/api/keys", json={"name": "v1_tester"})
    test_key = key_res.json()["key"]["key"]
    test_key_id = key_res.json()["key"]["id"]

    try:
        # Authenticated call
        auth_res = client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {test_key}"},
            json={"messages": [{"role": "user", "content": "ping"}]}
        )
        assert auth_res.status_code == 200
        comp_data = auth_res.json()
        assert comp_data["object"] == "chat.completion"
        assert len(comp_data["choices"]) > 0

        # Anthropic Claude /v1/messages call
        claude_res = client.post(
            "/v1/messages",
            headers={"x-api-key": test_key},
            json={"model": "claude-3-7-sonnet", "messages": [{"role": "user", "content": "ping"}]}
        )
        assert claude_res.status_code == 200
        claude_data = claude_res.json()
        assert claude_data["type"] == "message"
        assert len(claude_data["content"]) > 0

    finally:
        client.delete(f"/api/keys/{test_key_id}")


def test_combos_and_mitm_apis(client):
    """Test model combos CRUD, failover test, and MITM inspector."""
    # Combos GET
    c_res = client.get("/api/combos")
    assert c_res.status_code == 200
    assert "combos" in c_res.json()

    # Combos POST
    create_c = client.post("/api/combos", json={
        "name": "test_combo_xyz",
        "strategy": "fallback",
        "models": ["codex", "tokenharbor"]
    })
    assert create_c.status_code == 200
    assert create_c.json()["success"] is True

    # Combos Test Failover
    sim_res = client.post("/api/combos/test", json={"combo": "test_combo_xyz"})
    assert sim_res.status_code == 200
    assert sim_res.json()["success"] is True
    assert "trace" in sim_res.json()

    # Combos DELETE
    del_c = client.delete("/api/combos/test_combo_xyz")
    assert del_c.status_code == 200

    # MITM GET
    mitm_res = client.get("/api/mitm/requests")
    assert mitm_res.status_code == 200
    assert "requests" in mitm_res.json()

    # MITM DELETE
    clear_mitm = client.delete("/api/mitm/requests")
    assert clear_mitm.status_code == 200
    assert clear_mitm.json()["success"] is True


def test_prompt_injection_and_rtk_apis(client):
    """Test Prompt Injection and RTK compressor APIs."""
    # Prompt Injection GET & POST
    p_get = client.get("/api/prompt-injection")
    assert p_get.status_code == 200

    p_post = client.post("/api/prompt-injection", json={
        "enabled": True,
        "scope": "global",
        "position": "append",
        "content": "You are a senior engineer."
    })
    assert p_post.status_code == 200
    assert p_post.json()["success"] is True

    # RTK GET & POST
    rtk_get = client.get("/api/rtk")
    assert rtk_get.status_code == 200

    # RTK Test Compress
    sample_text = "Certainly! Here is the answer:\n\n\n\nconst x = 10;   \n\n\n\nHope this helps!"
    comp_res = client.post("/api/rtk/test-compress", json={"text": sample_text, "caveman_mode": True})
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert comp_data["success"] is True
    assert comp_data["compressed_chars"] < comp_data["original_chars"]
    assert comp_data["savings_pct"] > 0


def test_oauth_import_and_provider_sync(client):
    """Test OAuth import, auto-sync, and seamless sync with Apex provider manager & CLI."""
    # 1. OAuth Import for Antigravity
    res = client.post("/api/providers/oauth-import", json={"provider": "antigravity", "make_active": False})
    assert res.status_code == 200
    data = res.json()
    assert data["provider"] == "antigravity"
    assert "models" in data

    # 2. Auto-Sync all accounts & local engines
    sync_res = client.post("/api/providers/auto-sync")
    assert sync_res.status_code == 200
    sync_data = sync_res.json()
    assert sync_data["success"] is True
    assert "detected_accounts" in sync_data

    # 3. Test category batch test
    cat_res = client.post("/api/providers/test-category", json={"category": "oauth"})
    assert cat_res.status_code == 200
    assert cat_res.json()["category"] == "oauth"

    # 4. Add a compatible custom provider and verify instant appearance in shelf
    add_res = client.post("/api/providers/add", json={
        "name": "custom-openai-proxy",
        "base_url": "http://127.0.0.1:9999/v1",
        "api_key": "sk-custom-test",
        "models": ["custom-model-v1"],
        "auto_fetch": False,
        "verify_now": False
    })
    assert add_res.status_code == 200
    assert add_res.json()["success"] is True

    # Check that it appears in providers list endpoint
    provs_res = client.get("/api/providers")
    assert provs_res.status_code == 200
    p_shelf = provs_res.json()["providers"]
    found_custom = any(p["id"] == "custom-openai-proxy" for p in p_shelf)
    assert found_custom is True


def test_thinking_extraction_and_cross_surface_reasoning(client, monkeypatch):
    """Test OhMyRouter bidirectional reasoning: extract <think> and stream/return native reasoning blocks."""
    from apex.gateways import web_dashboard
    from apex.gateways.web_dashboard import extract_thinking_and_content, preflight_and_normalize_request

    # Unit test extraction
    raw = "<think>Step 1: Compute square root of 64 = 8.\nStep 2: Add 2 = 10.</think>The final result is 10."
    thinking, answer = extract_thinking_and_content(raw)
    assert "Step 1: Compute square root" in thinking
    assert "The final result is 10." in answer
    assert "<think>" not in answer

    # Mock agent run to return raw think tag
    monkeypatch.setattr(web_dashboard.default_agent, "run", lambda **kwargs: raw)

    # 1. Non-streaming OpenAI format (/v1/chat/completions)
    res_chat = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer sk-apex-master-live"},
        json={"model": "deepseek-reasoner", "messages": [{"role": "user", "content": "Compute sqrt(64) + 2"}]}
    )
    assert res_chat.status_code == 200
    chat_data = res_chat.json()
    msg = chat_data["choices"][0]["message"]
    assert "The final result is 10." in msg["content"]
    assert "Step 1: Compute square root" in msg["reasoning_content"]

    # 2. Non-streaming Claude format (/v1/messages)
    res_claude = client.post(
        "/v1/messages",
        headers={"x-api-key": "sk-apex-master-live"},
        json={"model": "claude-3-7-sonnet", "messages": [{"role": "user", "content": "Compute sqrt(64) + 2"}]}
    )
    assert res_claude.status_code == 200
    claude_data = res_claude.json()
    blocks = claude_data["content"]
    assert len(blocks) == 2
    assert blocks[0]["type"] == "thinking"
    assert "Step 1: Compute square root" in blocks[0]["thinking"]
    assert blocks[0]["signature"] == "apex-omop-verified"
    assert blocks[1]["type"] == "text"
    assert "The final result is 10." in blocks[1]["text"]

    # 3. Streaming OpenAI format (/v1/chat/completions)
    res_stream_chat = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer sk-apex-master-live"},
        json={"model": "deepseek-reasoner", "stream": True, "messages": [{"role": "user", "content": "Compute sqrt(64) + 2"}]}
    )
    assert res_stream_chat.status_code == 200
    assert "reasoning_content" in res_stream_chat.text
    assert "The final result is 10." in res_stream_chat.text

    # 4. Streaming Claude format (/v1/messages)
    res_stream_claude = client.post(
        "/v1/messages",
        headers={"x-api-key": "sk-apex-master-live"},
        json={"model": "claude-3-7-sonnet", "stream": True, "messages": [{"role": "user", "content": "Compute sqrt(64) + 2"}]}
    )
    assert res_stream_claude.status_code == 200
    assert "thinking_delta" in res_stream_claude.text
    assert "text_delta" in res_stream_claude.text


def test_per_key_sliding_rate_limit_and_quota(client, monkeypatch):
    """Test sliding-window RPM rate limiting and token quota exhaustion."""
    from apex.gateways import web_dashboard
    from apex.gateways.web_dashboard import KEYS_FILE, get_api_keys_storage, KEY_REQUEST_TIMESTAMPS

    monkeypatch.setattr(web_dashboard.default_agent, "run", lambda **kwargs: "Mocked completion response token usage test.")

    test_key_str = "sk-9r-test-quota-rate-limit-token-12345"
    key_entry = {
        "id": "key_test_quota",
        "name": "Quota Test Key",
        "key": test_key_str,
        "is_active": True,
        "created_at": "2026-11-09",
        "quota": "15 / 24h",   # very small quota: 15 tokens
        "rpm": 2,              # very low RPM: 2 requests per minute
        "used_tokens": 0
    }
    keys = get_api_keys_storage()
    keys.append(key_entry)
    KEYS_FILE.write_text(json.dumps(keys, indent=2))
    KEY_REQUEST_TIMESTAMPS["key_test_quota"].clear()

    try:
        # Request 1: should succeed (tokens recorded will exceed 15 tokens)
        res1 = client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {test_key_str}"},
            json={"model": "mimo-v2.6-flash:free", "messages": [{"role": "user", "content": "Hello test"}]}
        )
        assert res1.status_code == 200

        # Request 2: should be blocked with 429 due to exhausted quota!
        res2 = client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {test_key_str}"},
            json={"model": "mimo-v2.6-flash:free", "messages": [{"role": "user", "content": "Hello test 2"}]}
        )
        assert res2.status_code == 429
        assert "quota exhausted" in res2.json()["detail"]["error"]["message"].lower()

    finally:
        clean_keys = [k for k in get_api_keys_storage() if k["id"] != "key_test_quota"]
        KEYS_FILE.write_text(json.dumps(clean_keys, indent=2))


def test_preflight_normalization_and_ssrf_guard(client):
    """Test capability preflight for reasoning models and SSRF cloud metadata blocker."""
    from apex.gateways.web_dashboard import preflight_and_normalize_request, is_safe_upstream_url

    # Reasoning preflight checks
    raw_payload = {
        "model": "o3-mini",
        "temperature": 0.7,
        "top_p": 0.9,
        "presence_penalty": 0.5,
        "max_tokens": 1024,
        "messages": [
            {"role": "system", "content": "You are a coding specialist."},
            {"role": "user", "content": "Write quicksort in python"}
        ]
    }
    norm = preflight_and_normalize_request(raw_payload, "o3-mini")
    assert "temperature" not in norm
    assert "top_p" not in norm
    assert "presence_penalty" not in norm
    assert "max_tokens" not in norm
    assert norm["max_completion_tokens"] == 1024
    assert norm["messages"][0]["role"] == "developer"

    # SSRF guard checks
    assert is_safe_upstream_url("http://169.254.169.254/latest/meta-data") is False
    assert is_safe_upstream_url("http://metadata.google.internal/computeMetadata/v1/") is False
    assert is_safe_upstream_url("https://api.openai.com/v1") is True

    # Reject dangerous metadata URL via API
    add_ssrf = client.post("/api/providers/add", json={
        "name": "malicious-meta-provider",
        "base_url": "http://169.254.169.254/latest/meta-data",
        "api_key": "dummy",
        "auto_fetch": False,
        "verify_now": False
    })
    assert add_ssrf.status_code == 200
    assert add_ssrf.json()["success"] is False
    assert "SSRF Guard" in add_ssrf.json()["message"]






