"""Unit tests for Unified Ecosystem Auto-Discovery: MCP, Modular Skills & Custom Tools."""
import json
from pathlib import Path

from apex.config import CUSTOM_TOOLS_DIR, DATA_DIR
from apex.tools.mcp import mcp_manager
from apex.learning.skills import skill_manager
from apex.tools import tool_registry
from apex.tools.custom_loader import custom_tool_loader


def test_mcp_multi_path_discovery():
    """Verify that MCPClientManager discovers external MCP configs (e.g. Gemini instabox)."""
    tools = mcp_manager.discover_all_tools(force_refresh=True)
    assert isinstance(tools, dict)
    
    servers = mcp_manager.get_detected_servers()
    assert len(servers) >= 1
    
    server_names = [s["name"] for s in servers]
    assert "instabox" in server_names
    
    instabox_srv = next(s for s in servers if s["name"] == "instabox")
    assert instabox_srv["status"] == "online"
    assert instabox_srv["tool_count"] >= 10
    assert "mcp__instabox__create_machine" in tools
    assert "mcp__instabox__exec" in tools


def test_skills_multi_path_discovery():
    """Verify that SkillManager discovers skills from Gemini and Antigravity."""
    skill_manager.reload_skills()
    skills = skill_manager.get_detected_skills()
    assert len(skills) >= 15

    names = [s["name"] for s in skills]
    # Check Gemini skills
    assert "instabox" in names or "instabox-basic-setup" in names
    # Check Antigravity skills
    assert "agy-customizations" in names or "antigravity-guide" in names

    # Verify prompt formatting
    prompt_snippet = skill_manager.list_skills_for_prompt()
    assert "[Available Skills" in prompt_snippet
    assert "instabox" in prompt_snippet or "antigravity" in prompt_snippet


def test_custom_user_tools_loader(tmp_path):
    """Verify that custom Python scripts are dynamically imported and callable as tools."""
    custom_dir = CUSTOM_TOOLS_DIR
    custom_dir.mkdir(parents=True, exist_ok=True)
    test_script = custom_dir / "temp_unit_tool.py"
    
    script_content = '''"""Temporary unit test tool."""
TOOL_NAME = "unit_echo"
TOOL_DESCRIPTION = "Echoes input back"
TOOL_PARAMETERS = {
    "type": "object",
    "properties": {
        "text": {"type": "string"}
    },
    "required": ["text"]
}
def execute(args):
    return True, f"ECHO:{args.get('text', '')}"
'''
    test_script.write_text(script_content)

    try:
        tool_registry.discover_custom_tools(force_reload=True)
        custom_tools = tool_registry.get_custom_tools()
        assert "unit_echo" in custom_tools

        success, out = tool_registry.execute_tool("unit_echo", {"text": "hello_apex"})
        assert success is True
        assert "ECHO:hello_apex" in out
    finally:
        test_script.unlink(missing_ok=True)
        tool_registry.discover_custom_tools(force_reload=True)
        assert "unit_echo" not in tool_registry.get_custom_tools()


def test_tool_definitions_for_llm():
    """Verify all tool definitions (native + mcp) are properly packaged for the model."""
    all_defs = tool_registry.get_all_tool_definitions()
    assert len(all_defs) >= 25

    names = [d["function"]["name"] for d in all_defs]
    # Native tools
    assert "run_shell" in names
    assert "read_file" in names
    assert "edit_file" in names
    # MCP tools
    assert any(n.startswith("mcp__instabox__") for n in names)
