"""Unit tests for Cron & Scheduled Tasks Tools."""
import pytest
from apex.tools.scheduler_ops import manage_scheduled_tasks


def test_manage_scheduled_tasks_workflow():
    # 1. Add job
    add_res = manage_scheduled_tasks("add", name="test_backup", interval_minutes=30, prompt="Backup database sekarang")
    assert "Tugas Terjadwal Berhasil Dibuat" in add_res
    assert "test_backup" in add_res

    # 2. List jobs
    list_res = manage_scheduled_tasks("list")
    assert "test_backup" in list_res
    assert "30.0 menit" in list_res or "30 menit" in list_res

    # 3. Remove job
    del_res = manage_scheduled_tasks("remove", name="test_backup")
    assert "Tugas Dihapus" in del_res


def test_manage_scheduled_tasks_invalid():
    res = manage_scheduled_tasks("unknown_action")
    assert "tidak dikenali" in res
