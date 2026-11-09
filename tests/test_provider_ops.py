"""Unit tests for AI Provider Search, Smart Addition, and Agent Management Tool."""
import pytest
from apex.config import config
from apex.router.provider_manager import provider_manager
from apex.tools.provider_ops import manage_ai_providers
from fastapi.testclient import TestClient
from apex.gateways.web_dashboard import app


@pytest.fixture
def client():
    return TestClient(app)


def test_provider_manager_search():
    # Search by provider name
    res_deepseek = provider_manager.search_providers("deepseek")
    assert len(res_deepseek) > 0
    assert any("deepseek" in r["id"] for r in res_deepseek)

    # Search by model
    res_sonnet = provider_manager.search_providers("sonnet")
    assert len(res_sonnet) > 0

    # Search by category/feature keyword: free
    res_free = provider_manager.search_providers("free")
    assert len(res_free) > 0
    assert any(r["id"] in ["tokenharbor", "antigravity", "kiro", "ollama"] for r in res_free)

    # Search by fast keyword
    res_fast = provider_manager.search_providers("fast")
    assert len(res_fast) > 0
    assert any(r["id"] in ["groq", "cerebras", "sambanova", "together"] for r in res_fast)


def test_provider_manager_add_smart_and_use():
    # Smart add catalog provider 'groq'
    ok, msg, detail = provider_manager.add_provider_smart(
        "groq",
        api_key="gsk_testdummy123456789",
        verify_now=False
    )
    assert ok is True
    assert detail["id"] == "groq"
    assert "groq.com" in detail["base_url"]
    assert len(detail["models"]) > 0

    # Test switching provider
    first_model = detail["models"][0]
    switch_ok, switch_msg = provider_manager.set_active_provider("groq", first_model)
    assert switch_ok is True
    assert config.active_provider == "groq"
    assert config.default_model == first_model

    # Switch back to tokenharbor
    provider_manager.set_active_provider("tokenharbor", "mimo-v2.6-flash:free")
    assert config.active_provider == "tokenharbor"


def test_manage_ai_providers_tool():
    # 1. list
    list_res = manage_ai_providers("list")
    assert "Daftar Provider AI" in list_res

    # 2. search
    search_res = manage_ai_providers("search", query="deepseek")
    assert "deepseek" in search_res.lower()

    # 3. add
    add_res = manage_ai_providers(
        "add",
        provider_name="test_provider_x",
        base_url="http://localhost:9999/v1",
        model_name="model-x"
    )
    assert "Berhasil Dikonfigurasi" in add_res

    # 4. use
    use_res = manage_ai_providers("use", provider_name="test_provider_x", model_name="model-x")
    assert "test_provider_x" in use_res

    # 5. remove
    manage_ai_providers("use", provider_name="tokenharbor", model_name="mimo-v2.6-flash:free")
    rm_res = manage_ai_providers("remove", provider_name="test_provider_x")
    assert "Berhasil Dihapus" in rm_res


def test_web_providers_endpoints(client):
    # GET /api/providers
    res = client.get("/api/providers")
    assert res.status_code == 200
    data = res.json()
    assert "providers" in data
    assert "active_provider" in data
    assert len(data["providers"]) > 10

    # GET /api/providers/search
    search_res = client.get("/api/providers/search?q=groq")
    assert search_res.status_code == 200
    s_data = search_res.json()
    assert len(s_data["matches"]) > 0

    # POST /api/providers/add
    add_res = client.post("/api/providers/add", json={
        "name": "web_dummy_prov",
        "api_key": "dummy_key",
        "base_url": "http://127.0.0.1:8999/v1",
        "models": ["dummy-v1"],
        "verify_now": False
    })
    assert add_res.status_code == 200
    assert add_res.json()["success"] is True

    # POST /api/providers/use
    use_res = client.post("/api/providers/use", json={
        "provider": "web_dummy_prov",
        "model": "dummy-v1"
    })
    assert use_res.status_code == 200

    # Clean up and switch back
    client.post("/api/providers/use", json={"provider": "tokenharbor", "model": "mimo-v2.6-flash:free"})
    rm_res = client.post("/api/providers/remove", json={"name": "web_dummy_prov"})
    assert rm_res.status_code == 200
