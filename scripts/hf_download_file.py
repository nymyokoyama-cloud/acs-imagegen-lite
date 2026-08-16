from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from huggingface_hub import hf_hub_download


ALLOWED_REVISIONS = {
    "Comfy-Org/Krea-2": "952f49d49653cb42e7d6cf7cbfad74738073ec7d",
    "Comfy-Org/MiniMax-H3": "014cd40f7e177756c6b2473c0d93b1c89a790dd2",
    "Comfy-Org/z_image_turbo": "d24c4cf2a0cd98a42f23467e27e3d76ee9438b8e",
}


def _safe_relative(value: str, label: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not path.name:
        raise ValueError(f"{label} is not safe")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Download one pinned ACS ImageGen Lite model file")
    parser.add_argument("repo_id")
    parser.add_argument("revision")
    parser.add_argument("filename")
    parser.add_argument("local_dir")
    # Comfy-Orgのリパックは`split_files/`配下にあるため、取得後にComfyUIの配置パスへ移す。
    parser.add_argument("local_path", nargs="?", default=None)
    args = parser.parse_args()

    if ALLOWED_REVISIONS.get(args.repo_id) != args.revision:
        raise ValueError("Repository or revision is not in the ACS model allowlist")
    filename = _safe_relative(args.filename, "Model filename")
    local_path = _safe_relative(args.local_path, "Model local path") if args.local_path else filename

    local_dir = Path(args.local_dir).resolve()
    local_dir.mkdir(parents=True, exist_ok=True)
    # The revision is checked against the immutable repository allowlist above.
    downloaded = Path(
        hf_hub_download(  # nosec B615
            repo_id=args.repo_id,
            filename=args.filename,
            revision=args.revision,
            local_dir=local_dir,
        )
    ).resolve()
    expected = (local_dir / filename).resolve()
    if downloaded != expected or not downloaded.is_file():
        raise RuntimeError("Hugging Face download did not create the expected local file")

    final = (local_dir / local_path).resolve()
    if final != downloaded:
        if not str(final).startswith(str(local_dir) + os.sep):
            raise ValueError("Model local path escapes the model root")
        final.parent.mkdir(parents=True, exist_ok=True)
        os.replace(downloaded, final)
        for parent in downloaded.parents:
            if parent == local_dir:
                break
            try:
                parent.rmdir()
            except OSError:
                break
    print(json.dumps({"ok": True, "path": str(final)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
