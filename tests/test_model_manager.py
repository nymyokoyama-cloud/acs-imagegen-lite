from __future__ import annotations

import hashlib
import importlib.util
import sys
import time
from pathlib import Path

import pytest

from app import config, model_manager


def _load_download_script():
    path = Path(__file__).resolve().parents[1] / "scripts" / "hf_download_file.py"
    spec = importlib.util.spec_from_file_location("acs_hf_download_file", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


hf_download_file = _load_download_script()


def test_model_status_exposes_beginner_packages_and_free_space() -> None:
    status = model_manager.public_status()
    packages = {item["key"]: item for item in status["packages"]}
    assert set(packages) == {"turbo", "raw", "all", "zimage", "h3", "recommended", "everything"}
    assert packages["turbo"]["size"] < packages["all"]["size"]
    assert packages["recommended"]["requires_h3_terms"] is True
    assert packages["recommended"]["requires_krea_terms"] is True
    assert packages["h3"]["requires_krea_terms"] is False
    assert status["free_bytes"] > 0


def test_zimage_package_is_the_lightest_and_needs_no_terms() -> None:
    packages = {item["key"]: item for item in model_manager.public_status()["packages"]}
    zimage = packages["zimage"]
    # Apache-2.0のため、Krea 2やH3のような同意ゲートは付けない。
    assert zimage["requires_krea_terms"] is False
    assert zimage["requires_h3_terms"] is False
    assert zimage["size"] == 6_201_001_296 + 5_631_994_051 + 335_304_388
    assert zimage["size"] < packages["turbo"]["size"]
    assert packages["everything"]["size"] == packages["all"]["size"] + zimage["size"] + packages["h3"]["size"]


def test_zimage_files_are_pinned_to_the_official_repack_revision() -> None:
    for key in config.ZIMAGE_FILE_KEYS:
        entry = config.MODEL_FILES[key]
        assert entry["repo_id"] == "Comfy-Org/z_image_turbo"
        assert entry["revision"] == "d24c4cf2a0cd98a42f23467e27e3d76ee9438b8e"
        assert entry["revision"] in str(entry["repository"])
        # 取得元は`split_files/`配下、配置先はComfyUIのフォルダ構成。
        assert str(entry["remote_path"]).startswith("split_files/")
        assert str(entry["remote_path"]).endswith(str(entry["relative_path"]))
        assert len(str(entry["sha256"])) == 64
        assert int(entry["size"]) > 0
    assert hf_download_file.ALLOWED_REVISIONS["Comfy-Org/z_image_turbo"] == (
        "d24c4cf2a0cd98a42f23467e27e3d76ee9438b8e"
    )


def test_repacked_file_is_moved_from_split_files_to_the_comfyui_folder(tmp_path, monkeypatch) -> None:
    local_dir = tmp_path / "models"
    source = local_dir / "split_files" / "vae" / "ae.safetensors"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"vae-bytes")

    def fake_download(repo_id, filename, revision, local_dir):  # noqa: ANN001
        return str(Path(local_dir) / filename)

    monkeypatch.setattr(hf_download_file, "hf_hub_download", fake_download)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "hf_download_file.py",
            "Comfy-Org/z_image_turbo",
            "d24c4cf2a0cd98a42f23467e27e3d76ee9438b8e",
            "split_files/vae/ae.safetensors",
            str(local_dir),
            "vae/ae.safetensors",
        ],
    )
    hf_download_file.main()

    assert (local_dir / "vae" / "ae.safetensors").read_bytes() == b"vae-bytes"
    assert not (local_dir / "split_files").exists()


def test_download_script_rejects_paths_outside_the_model_root(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "hf_download_file.py",
            "Comfy-Org/z_image_turbo",
            "d24c4cf2a0cd98a42f23467e27e3d76ee9438b8e",
            "split_files/vae/ae.safetensors",
            str(tmp_path),
            "../escaped.safetensors",
        ],
    )
    with pytest.raises(ValueError, match="not safe"):
        hf_download_file.main()


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
