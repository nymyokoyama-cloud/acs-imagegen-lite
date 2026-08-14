from __future__ import annotations

import hashlib
import time
from pathlib import Path

from app import model_manager


def test_model_status_exposes_beginner_packages_and_free_space() -> None:
    status = model_manager.public_status()
    packages = {item["key"]: item for item in status["packages"]}
    assert set(packages) == {"turbo", "raw", "all", "h3", "recommended", "everything"}
    assert packages["turbo"]["size"] < packages["all"]["size"]
    assert packages["recommended"]["requires_h3_terms"] is True
    assert status["free_bytes"] > 0


def test_unknown_package_is_rejected_before_download() -> None:
    try:
        model_manager.start_install("unknown")
    except RuntimeError as exc:
        assert "無効" in str(exc)
    else:
        raise AssertionError("download should be disabled in tests")


def test_small_official_style_package_downloads_and_verifies(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    model_root = tmp_path / "models"
    data_root = tmp_path / "data"
    source.mkdir()
    model_root.mkdir()
    data_root.mkdir()
    payloads = {
        "text_encoder": ("text_encoders/text.bin", b"text-encoder"),
        "vae": ("vae/vae.bin", b"vae"),
        "turbo": ("diffusion_models/turbo.bin", b"turbo-model"),
    }
    files = {}
    for key, (relative, payload) in payloads.items():
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        files[key] = {
            "relative_path": relative,
            "size": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    packages = {
        "turbo": {
            "label": "Turbo",
            "description": "test",
            "file_keys": ("text_encoder", "vae", "turbo"),
        }
    }
    monkeypatch.setattr(model_manager, "MODEL_ROOT", model_root)
    monkeypatch.setattr(model_manager, "MODEL_STATE_FILE", data_root / "state.json")
    monkeypatch.setattr(model_manager, "MODEL_VERIFIED_FILE", data_root / "verified.json")
    monkeypatch.setattr(model_manager, "ACTIVITY_FILE", data_root / "activity")
    monkeypatch.setattr(model_manager, "MODEL_REPOSITORY", source.as_uri())
    monkeypatch.setattr(model_manager, "MODEL_FILES", files)
    monkeypatch.setattr(model_manager, "MODEL_PACKAGES", packages)
    monkeypatch.setattr(model_manager, "DISABLE_MODEL_DOWNLOAD", False)
    monkeypatch.setattr(model_manager, "DOWNLOAD_THREAD", None)
    monkeypatch.setattr(model_manager, "CURRENT_STATE", model_manager._default_state())

    model_manager.start_install("turbo")
    deadline = time.time() + 5
    while time.time() < deadline:
        state = model_manager.public_status()["state"]
        if state["status"] in {"complete", "error", "canceled"}:
            break
        time.sleep(0.02)
    assert state["status"] == "complete", state
    assert all(item["verified"] for item in model_manager.public_status()["files"])
    for key, (relative, payload) in payloads.items():
        assert (model_root / relative).read_bytes() == payload
