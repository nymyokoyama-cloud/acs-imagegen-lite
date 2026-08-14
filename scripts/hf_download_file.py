from __future__ import annotations

import argparse
import json
from pathlib import Path

from huggingface_hub import hf_hub_download


def main() -> None:
    parser = argparse.ArgumentParser(description="Download one pinned ACS ImageGen Lite model file")
    parser.add_argument("repo_id")
    parser.add_argument("filename")
    parser.add_argument("local_dir")
    args = parser.parse_args()

    local_dir = Path(args.local_dir).resolve()
    local_dir.mkdir(parents=True, exist_ok=True)
    downloaded = Path(
        hf_hub_download(
            repo_id=args.repo_id,
            filename=args.filename,
            local_dir=local_dir,
        )
    ).resolve()
    expected = (local_dir / args.filename).resolve()
    if downloaded != expected or not downloaded.is_file():
        raise RuntimeError("Hugging Face download did not create the expected local file")
    print(json.dumps({"ok": True, "path": str(downloaded)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
