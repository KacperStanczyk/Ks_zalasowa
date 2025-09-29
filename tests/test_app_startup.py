import os
import sys
from pathlib import Path

import pytest

# Ensure the Qt platform is set to offscreen to avoid display requirements
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

try:  # pragma: no cover - optional dependency
    pytest.importorskip("PySide6")
    import app
except ImportError as exc:  # pragma: no cover - optional dependency
    pytest.skip(f"PySide6 runtime dependencies missing: {exc}", allow_module_level=True)


def test_main_starts(monkeypatch, tmp_path):
    """Application main should initialize and exit cleanly."""
    config = app.DEFAULT_CONFIG.copy()
    config["db_plain_path"] = str(tmp_path / "data" / "app.db")
    config["db_encrypted_path"] = str(tmp_path / "data" / "app.db.enc")
    config["backup_path"] = str(tmp_path / "backup")

    # Avoid external side effects during test
    monkeypatch.setattr(app, "load_config", lambda: config)
    monkeypatch.setattr(app, "decrypt_file", lambda *a, **k: None)
    monkeypatch.setattr(app, "encrypt_file", lambda *a, **k: None)
    monkeypatch.setattr(app, "secure_delete", lambda *a, **k: None)
    monkeypatch.setattr(app, "local_backup", lambda *a, **k: None)

    # Do not enter the Qt event loop
    monkeypatch.setattr(app.QApplication, "exec", lambda self: 0)

    assert app.main() == 0

