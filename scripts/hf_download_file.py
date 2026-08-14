from __future__ import annotations

import argparse
import json
from pathlib import Path

from huggingface_hub import hf_hub_download


ALLOWED_REVISIONS = {
    "Comfy-Org/Krea-2": "952f49d49653cb42e7d6cf7cbfad74738073ec7d",
    "Comfy-Org/MiniMax-H3": "014cd40f7e177756c6b2473c0d93b1c89a790dd2",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Download one pinned ACS ImageGen Lite model file")
    parser.add_argument("repo_id")
    parser.add_argument("revision")
    parser.add_argument("filename")
    parser.add_argument("local_dir")
    args = parser.parse_args()

    if ALLOWED_REVISIONS.get(args.repo_id) != args.revision:
        raise ValueError("Repository or revision is not in the ACS model allowlist")
    filename = Path(args.filename)
    if filename.is_absolute() or ".." in filename.parts:
        raise ValueError("Model filename is not safe")

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
    expected = (local_dir / args.filename).resolve()
    if downloaded != expected or not downloaded.is_file():
        raise RuntimeError("Hugging Face download did not create the expected local file")
    print(json.dumps({"ok": True, "path": str(downloaded)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
