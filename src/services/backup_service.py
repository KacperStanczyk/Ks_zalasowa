"""Backup helpers."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional


def rotate_backups(backup_dir: Path) -> None:
    files = sorted(backup_dir.glob("*.enc"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in files[2:]:
        old.unlink()


def local_backup(enc_db_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    dest = backup_dir / f"app.db.enc.bak"
    shutil.copy2(enc_db_path, dest)
    rotate_backups(backup_dir)
    return dest


def drive_backup(path: Path, drive_folder_id: str) -> None:
    # Placeholder: integrate google drive API
    pass
