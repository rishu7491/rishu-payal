"""Backup and Disaster Recovery Manager for Payal AI."""

import os
import shutil
import time
import zipfile
from typing import Any, Dict, List, Optional
from core.identity.config import CONFIG


class BackupManager:
    """Manages snapshot backups and safe rollbacks of memory DB and configuration."""

    def __init__(self, backup_dir: Optional[str] = None):
        base_dir = getattr(getattr(CONFIG, "storage", None), "base_dir", "data")
        self.backup_dir = backup_dir or os.path.join(base_dir, "backups")
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self, tag: Optional[str] = None) -> Dict[str, Any]:
        """Create a compressed snapshot of current memory store and configuration."""
        now = int(time.time())
        tag_str = f"_{tag}" if tag else ""
        backup_filename = f"payal_backup_{now}{tag_str}.zip"
        backup_path = os.path.join(self.backup_dir, backup_filename)

        files_to_backup = [
            os.path.join("data", "memory.db"),
            os.path.join("data", "audit_ledger.jsonl"),
            os.path.join("config", "payal_config.json"),
            "payal.env",
        ]

        included_files = []
        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for filepath in files_to_backup:
                if os.path.exists(filepath):
                    arcname = os.path.basename(filepath)
                    zipf.write(filepath, arcname=arcname)
                    included_files.append(filepath)

        size_kb = os.path.getsize(backup_path) / 1024.0 if os.path.exists(backup_path) else 0.0

        return {
            "success": True,
            "backup_id": f"bak-{now}",
            "filename": backup_filename,
            "path": os.path.abspath(backup_path),
            "size_kb": round(size_kb, 2),
            "included_files": included_files,
            "timestamp": now,
        }

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available snapshot backups."""
        if not os.path.exists(self.backup_dir):
            return []

        backups = []
        for fname in os.listdir(self.backup_dir):
            if fname.endswith(".zip") and fname.startswith("payal_backup_"):
                fpath = os.path.join(self.backup_dir, fname)
                stat = os.stat(fpath)
                backups.append({
                    "filename": fname,
                    "path": os.path.abspath(fpath),
                    "size_kb": round(stat.st_size / 1024.0, 2),
                    "created_at": stat.st_mtime,
                })
        # Sort newest first
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups

    def restore_backup(self, backup_name: str) -> Dict[str, Any]:
        """Restore memory database and configuration from a snapshot backup."""
        target_path = os.path.join(self.backup_dir, backup_name) if not os.path.isabs(backup_name) else backup_name
        if not os.path.exists(target_path):
            return {"success": False, "error": f"Backup file not found: {backup_name}"}

        # 1. Create safety checkpoint of current state before restoring
        safety = self.create_backup(tag="pre_restore_safety")

        # 2. Extract into current project root
        restored_files = []
        with zipfile.ZipFile(target_path, "r") as zipf:
            for item in zipf.infolist():
                if item.filename == "memory.db":
                    dest = os.path.join("data", "memory.db")
                    with zipf.open(item) as src, open(dest, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    restored_files.append(dest)
                elif item.filename == "audit_ledger.jsonl":
                    dest = os.path.join("data", "audit_ledger.jsonl")
                    with zipf.open(item) as src, open(dest, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    restored_files.append(dest)

        return {
            "success": True,
            "restored_from": backup_name,
            "safety_checkpoint": safety.get("filename"),
            "restored_files": restored_files,
            "timestamp": time.time(),
        }


BACKUP_MANAGER = BackupManager()

