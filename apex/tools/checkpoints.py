"""Automatic Pre-Write Checkpoints & undo_file Safety Net (Zeline Style)."""
from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from apex.config import CHECKPOINTS_DIR


class CheckpointManager:
    """Manages file snapshots and atomic undo operations."""

    def __init__(self) -> None:
        CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
        self.meta_file = CHECKPOINTS_DIR / "meta.json"
        self._meta: Dict[str, List[Dict[str, Any]]] = {}
        self._load_meta()

    def _load_meta(self) -> None:
        if self.meta_file.exists():
            try:
                with open(self.meta_file, "r", encoding="utf-8") as f:
                    self._meta = json.load(f)
            except Exception:
                self._meta = {}

    def _save_meta(self) -> None:
        try:
            with open(self.meta_file, "w", encoding="utf-8") as f:
                json.dump(self._meta, f, indent=2)
        except Exception:
            pass

    def snapshot_file(self, file_path: Path | str) -> Optional[str]:
        """Save a snapshot of the file before it gets modified."""
        p = Path(file_path).resolve()
        if not p.exists() or not p.is_file():
            # If file doesn't exist yet, record that it was created so undo can delete it
            key = str(p)
            if key not in self._meta:
                self._meta[key] = []
            self._meta[key].append({
                "timestamp": time.time(),
                "snapshot_path": None,
                "was_new": True
            })
            self._save_meta()
            return None

        # Hash path to create clean backup location
        path_hash = hashlib.sha256(str(p).encode("utf-8")).hexdigest()[:16]
        ts = int(time.time() * 1000)
        snap_dir = CHECKPOINTS_DIR / path_hash
        snap_dir.mkdir(parents=True, exist_ok=True)
        snap_file = snap_dir / f"{ts}_{p.name}"

        try:
            shutil.copy2(p, snap_file)
            key = str(p)
            if key not in self._meta:
                self._meta[key] = []
            self._meta[key].append({
                "timestamp": time.time(),
                "snapshot_path": str(snap_file),
                "was_new": False
            })
            self._save_meta()
            return str(snap_file)
        except Exception:
            return None

    def undo_file(self, file_path: Path | str) -> tuple[bool, str]:
        """Revert a file to its most recent pre-write snapshot."""
        p = Path(file_path).resolve()
        key = str(p)

        history = self._meta.get(key, [])
        if not history:
            return False, f"No previous checkpoint found for '{p}'"

        last_entry = history.pop()
        self._save_meta()

        if last_entry.get("was_new"):
            # File was created; undo means delete it
            if p.exists():
                try:
                    p.unlink()
                    return True, f"Undo successful: Removed newly created file '{p.name}'"
                except Exception as e:
                    return False, f"Failed to remove file during undo: {e}"
            return True, f"File '{p.name}' already removed"

        snap_path_str = last_entry.get("snapshot_path")
        if not snap_path_str or not Path(snap_path_str).exists():
            return False, f"Snapshot file missing for '{p.name}'"

        snap_path = Path(snap_path_str)
        try:
            shutil.copy2(snap_path, p)
            return True, f"Undo successful: Restored '{p.name}' from snapshot ({snap_path.name})"
        except Exception as e:
            return False, f"Failed to restore file from snapshot: {e}"

    def list_checkpoints(self, file_path: Optional[Path | str] = None) -> List[Dict[str, Any]]:
        """List available snapshots for a specific file or all files."""
        if file_path:
            p = str(Path(file_path).resolve())
            return self._meta.get(p, [])
        
        all_snaps: list[dict[str, Any]] = []
        for path_str, records in self._meta.items():
            for rec in records:
                all_snaps.append({
                    "target_file": path_str,
                    "timestamp": rec["timestamp"],
                    "snapshot": rec["snapshot_path"],
                    "was_new": rec["was_new"]
                })
        return all_snaps


# Global checkpoint instance
checkpoint_manager = CheckpointManager()
