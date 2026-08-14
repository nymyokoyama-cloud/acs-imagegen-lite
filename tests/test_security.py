from __future__ import annotations

from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


def test_distribution_has_no_private_paths_or_identity_labels() -> None:
    forbidden = [
        "/Users/" + "user",
        "/Volumes/" + "ACS_DATA",
        ".runpod" + "_key",
        "MiniMax" + "-H3-Mac",
        "奈" + "々",
        "あ" + "きな",
    ]
    inspected = []
    for path in PROJECT.rglob("*"):
        if not path.is_file() or any(part.startswith(".venv") for part in path.parts):
            continue
        if path.suffix not in {".py", ".html", ".md", ".json", ".sh", ".txt"} and path.name not in {
            "Dockerfile"
        }:
            continue
        inspected.append(path)
        content = path.read_text(encoding="utf-8", errors="ignore")
        for value in forbidden:
            assert value not in content, f"private marker found in {path.relative_to(PROJECT)}"
    assert inspected


def test_distribution_contains_no_model_weights_or_secrets() -> None:
    banned_suffixes = {".safetensors", ".ckpt", ".pt", ".pth", ".gguf", ".pem", ".key"}
    banned_names = {".env", "id_rsa", "credentials.json"}
    for path in PROJECT.rglob("*"):
        if not path.is_file() or any(part.startswith(".venv") for part in path.parts):
            continue
        assert path.suffix.lower() not in banned_suffixes
        assert path.name not in banned_names

