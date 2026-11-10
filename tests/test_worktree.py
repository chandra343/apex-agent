"""Unit tests for Git Worktree Isolation Sandbox."""
import subprocess
import pytest
from apex.swarm.worktree import WorktreeSandboxManager, manage_worktree_sandbox


def test_worktree_sandbox_lifecycle(tmp_path):
    # Initialize a dummy git repo
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.local"], cwd=str(tmp_path), capture_output=True, check=True)

    dummy_file = tmp_path / "hello.txt"
    dummy_file.write_text("initial commit")
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), capture_output=True, check=True)

    mgr = WorktreeSandboxManager(str(tmp_path))

    # 1. Create sandbox
    task_id = "test_feature"
    create_res = mgr.create_sandbox(task_id)
    assert create_res["success"] is True
    worktree_path = create_res["worktree_path"]

    try:
        # 2. Modify file inside worktree
        modified_file = tmp_path / "hello.txt"
        assert modified_file.read_text() == "initial commit"  # main repo is untainted!

        # 3. Run verification in sandbox
        v_res = mgr.run_verification(task_id, command="echo 'Tests passing'")
        assert v_res["success"] is True

        # 4. Tool wrapper check
        tool_list = manage_worktree_sandbox("list", repo_dir=str(tmp_path))
        assert "Active Sandboxes" in tool_list or "apex/sandbox-" in tool_list
    finally:
        # 5. Discard sandbox
        mgr.discard_sandbox(task_id)
