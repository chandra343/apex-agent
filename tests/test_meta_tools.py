"""Unit tests for Meta-Tooling: Autonomous Tool, Skill & MCP Synthesis."""
from pathlib import Path
from apex.tools import tool_registry
from apex.learning.skills import skill_manager
from apex.config import CUSTOM_TOOLS_DIR, SKILLS_DIR
import shutil


def test_autonomous_create_custom_tool():
    """Verify create_custom_tool creates and hot-loads a tool into the registry."""
    tool_code = """
def execute(args):
    val = args.get("val", 0)
    return True, f"MultiplierResult: {val * 5}"
"""
    success, msg = tool_registry.execute_tool("create_custom_tool", {
        "name": "auto_multiplier_test",
        "description": "Multiplies input by 5",
        "parameters": {"type": "object", "properties": {"val": {"type": "integer"}}},
        "python_code": tool_code
    })
    assert success is True
    assert "auto_multiplier_test" in tool_registry.get_custom_tools() or "custom__auto_multiplier_test" in tool_registry.get_custom_tools()

    # Call it immediately
    target_name = "auto_multiplier_test" if "auto_multiplier_test" in tool_registry._tools else "custom__auto_multiplier_test"
    call_ok, call_out = tool_registry.execute_tool(target_name, {"val": 10})
    assert call_ok is True
    assert "MultiplierResult: 50" in call_out

    # Cleanup
    (CUSTOM_TOOLS_DIR / "auto_multiplier_test.py").unlink(missing_ok=True)
    tool_registry.discover_custom_tools(force_reload=True)


def test_autonomous_create_skill():
    """Verify create_skill creates and hot-loads a modular skill package."""
    success, msg = tool_registry.execute_tool("create_skill", {
        "name": "auto-graphql-introspection",
        "description": "Skill for introspecting and analyzing GraphQL schemas",
        "instructions": "1. Query __schema\n2. Extract types and mutations\n3. Check sensitive queries"
    })
    assert success is True
    assert (SKILLS_DIR / "auto-graphql-introspection" / "SKILL.md").is_file()

    # Verify retrieval
    instructions = skill_manager.get_skill_instructions("auto-graphql-introspection")
    assert instructions is not None
    assert "Query __schema" in instructions

    # Cleanup
    shutil.rmtree(SKILLS_DIR / "auto-graphql-introspection", ignore_errors=True)
    skill_manager.reload_skills()
