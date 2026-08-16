from __future__ import annotations

import hashlib
import json
import os
import shutil
# Subprocess uses the fixed interpreter and allowlisted model arguments, never a shell.
import subprocess  # nosec B404
import sys
import threading
import time
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Any

from .config import (
    ACTIVITY_FILE,
    DISABLE_MODEL_DOWNLOAD,
    MODEL_FILES,
    MODEL_PACKAGES,
    MODEL_REPOSITORY,
    MODEL_ROOT,
    MODEL_STATE_FILE,
    MODEL_VERIFIED_FILE,
    PROJECT_DIR,
    VERSION,
    ensure_directories,
)


STATE_LOCK = threading.Lock()
CANCEL_EVENT = threading.Event()
DOWNLOAD_THREAD: threading.Thread | None = None
STATE_WRITE_INTERVAL = 0.5
HF_DOWNLOAD_SCRIPT = PROJECT_DIR / "scripts" / "hf_download_file.py"


def _default_state() -> dict[str, Any]:
    return {
        "status": "idle",
        "package": None,
        "file_key": None,
        "filename": None,
        "file_index": 0,
        "file_count": 0,
        "file_downloaded": 0,
        "file_size": 0,
        "total_downloaded": 0,
        "total_size": 0,
        "percent": 0.0,
        "message": "必要なモデルを選んでください",
        "error": None,
        "started_at": None,
        "finished_at": None,
    }


def _load_json(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else fallback.copy()
    except Exception:
        return fallback.copy()


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


ensure_directories()
CURRENT_STATE = _load_json(MODEL_STATE_FILE, _default_state())
if CURRENT_STATE.get("status") in {"downloading", "verifying"}:
    CURRENT_STATE.update(
        status="interrupted",
        message="前回の取得が中断されました。ボタンを押すと続きから再開します",
        error=None,
        finished_at=time.time(),
    )
    _atomic_json(MODEL_STATE_FILE, CURRENT_STATE)


def _set_state(**updates: Any) -> None:
    with STATE_LOCK:
        CURRENT_STATE.update(updates)
        _atomic_json(MODEL_STATE_FILE, CURRENT_STATE)
    ACTIVITY_FILE.touch(exist_ok=True)


def _verified_records() -> dict[str, Any]:
    return _load_json(MODEL_VERIFIED_FILE, {})


def _target(file_key: str) -> Path:
    return MODEL_ROOT / str(MODEL_FILES[file_key]["relative_path"])


def _record_is_current(file_key: str, path: Path, records: dict[str, Any]) -> bool:
    try:
        stat = path.stat()
        record = records.get(file_key, {})
        return (
            stat.st_size == int(MODEL_FILES[file_key]["size"])
            and record.get("sha256") == MODEL_FILES[file_key]["sha256"]
            and int(record.get("size", -1)) == stat.st_size
            and int(record.get("mtime_ns", -1)) == stat.st_mtime_ns
        )
    except OSError:
        return False


def _file_public_status(file_key: str, records: dict[str, Any]) -> dict[str, Any]:
    path = _target(file_key)
    partial = path.with_suffix(path.suffix + ".part")
    expected = int(MODEL_FILES[file_key]["size"])
    verified = _record_is_current(file_key, path, records)
    present = path.is_file() and path.stat().st_size == expected
    partial_size = min(partial.stat().st_size, expected) if partial.is_file() else 0
    return {
        "key": file_key,
        "filename": path.name,
        "expected_size": expected,
        "installed": present,
        "verified": verified,
        "partial_size": partial_size,
    }


def public_status() -> dict[str, Any]:
    records = _verified_records()
    files = {key: _file_public_status(key, records) for key in MODEL_FILES}
    packages: list[dict[str, Any]] = []
    for key, definition in MODEL_PACKAGES.items():
        selected = [files[file_key] for file_key in definition["file_keys"]]
        packages.append(
            {
                "key": key,
                "label": definition["label"],
                "description": definition["description"],
                "size": sum(int(MODEL_FILES[file_key]["size"]) for file_key in definition["file_keys"]),
                "installed": all(item["installed"] for item in selected),
                "verified": all(item["verified"] for item in selected),
                "partial_size": sum(item["partial_size"] for item in selected),
                "requires_krea_terms": bool(definition.get("requires_krea_terms", False)),
                "requires_h3_terms": bool(definition.get("requires_h3_terms", False)),
            }
        )
    with STATE_LOCK:
        state = CURRENT_STATE.copy()
    free = shutil.disk_usage(MODEL_ROOT).free
    return {
        "state": state,
        "packages": packages,
        "files": list(files.values()),
        "free_bytes": free,
        "download_disabled": DISABLE_MODEL_DOWNLOAD,
    }


def _sha256(path: Path, file_key: str, completed_before: int, total_size: int) -> str:
    digest = hashlib.sha256()
    file_size = path.stat().st_size
    processed = 0
    last_write = 0.0
    with path.open("rb") as handle:
        while chunk := handle.read(16 * 1024 * 1024):
            if CANCEL_EVENT.is_set():
                raise InterruptedError("取得を中断しました")
            digest.update(chunk)
            processed += len(chunk)
            now = time.monotonic()
            if now - last_write >= STATE_WRITE_INTERVAL:
                percent = 100 * (completed_before + processed) / max(1, total_size)
                _set_state(
                    status="verifying",
                    file_key=file_key,
                    filename=path.name,
                    file_downloaded=processed,
                    file_size=file_size,
                    total_downloaded=completed_before + processed,
                    percent=round(percent, 2),
                    message=f"{path.name} の安全確認中",
                )
                last_write = now
    return digest.hexdigest()


def _save_verified(file_key: str, path: Path) -> None:
    records = _verified_records()
    stat = path.stat()
    records[file_key] = {
        "sha256": MODEL_FILES[file_key]["sha256"],
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "verified_at": time.time(),
    }
    _atomic_json(MODEL_VERIFIED_FILE, records)


def _download_stream(url: str, partial: Path, expected_size: int, progress) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"https", "file"}:
        raise RuntimeError("モデル取得URLの方式が許可されていません")
    existing = partial.stat().st_size if partial.is_file() else 0
    if existing > expected_size:
        partial.rename(partial.with_suffix(partial.suffix + f".invalid.{int(time.time())}"))
        existing = 0
    request = urllib.request.Request(url, headers={"User-Agent": f"ACS-ImageGen-Lite/{VERSION}"})
    if existing:
        request.add_header("Range", f"bytes={existing}-")
    response = urllib.request.urlopen(request, timeout=60)  # nosec B310
    status = getattr(response, "status", None)
    if existing and status != 206:
        response.close()
        existing = 0
        request = urllib.request.Request(url, headers={"User-Agent": f"ACS-ImageGen-Lite/{VERSION}"})
        response = urllib.request.urlopen(request, timeout=60)  # nosec B310
    mode = "ab" if existing else "wb"
    downloaded = existing
    last_write = 0.0
    with response, partial.open(mode) as handle:
        while chunk := response.read(8 * 1024 * 1024):
            if CANCEL_EVENT.is_set():
                raise InterruptedError("取得を中断しました")
            handle.write(chunk)
            downloaded += len(chunk)
            now = time.monotonic()
            if now - last_write >= STATE_WRITE_INTERVAL:
                progress(downloaded)
                last_write = now
    progress(downloaded)
    if downloaded != expected_size:
        raise RuntimeError(f"受信サイズが一致しません: {downloaded} / {expected_size}")


def _download_huggingface(
    repo_id: str,
    revision: str,
    remote_path: str,
    relative_path: str,
    target: Path,
    expected_size: int,
    progress,
) -> None:
    env = os.environ.copy()
    env["HF_XET_HIGH_PERFORMANCE"] = "1"
    env["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    process = subprocess.Popen(
        [
            sys.executable,
            str(HF_DOWNLOAD_SCRIPT),
            repo_id,
            revision,
            remote_path,
            str(MODEL_ROOT),
            relative_path,
        ],  # nosec B603
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        while process.poll() is None:
            if CANCEL_EVENT.wait(STATE_WRITE_INTERVAL):
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                raise InterruptedError("取得を中断しました")
            visible_size = min(target.stat().st_size, expected_size) if target.is_file() else 0
            progress(visible_size)
        stdout, stderr = process.communicate()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
    if process.returncode != 0:
        detail = (stderr or stdout or "unknown error").strip().splitlines()[-1][:300]
        raise RuntimeError(f"Hugging Face高速取得に失敗しました: {detail}")
    if not target.is_file() or target.stat().st_size != expected_size:
        actual = target.stat().st_size if target.is_file() else 0
        raise RuntimeError(f"受信サイズが一致しません: {actual} / {expected_size}")
    progress(expected_size)


def _prepare_file(file_key: str, completed_before: int, total_size: int, index: int, count: int) -> None:
    definition = MODEL_FILES[file_key]
    target = _target(file_key)
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".part")
    expected_size = int(definition["size"])
    records = _verified_records()
    if _record_is_current(file_key, target, records):
        return

    if target.is_file():
        if target.stat().st_size == expected_size:
            _set_state(
                status="verifying",
                file_key=file_key,
                filename=target.name,
                file_index=index,
                file_count=count,
                file_size=expected_size,
                message=f"既存の {target.name} を安全確認中",
            )
            if _sha256(target, file_key, completed_before, total_size) == definition["sha256"]:
                _save_verified(file_key, target)
                return
        target.rename(target.with_suffix(target.suffix + f".invalid.{int(time.time())}"))

    repository = str(definition.get("repository", MODEL_REPOSITORY)).rstrip("/")
    # 取得元パスは配置パスと異なる場合がある（Comfy-Orgリパックの`split_files/`）。
    remote_path = str(definition.get("remote_path", definition["relative_path"]))
    url = f"{repository}/{remote_path}"
    accelerated = bool(definition.get("repo_id"))

    def progress(downloaded: int) -> None:
        total_downloaded = completed_before + downloaded
        _set_state(
            status="downloading",
            file_key=file_key,
            filename=target.name,
            file_index=index,
            file_count=count,
            file_downloaded=downloaded,
            file_size=expected_size,
            total_downloaded=total_downloaded,
            percent=round(100 * total_downloaded / max(1, total_size), 2),
            message=(
                f"{target.name} を高速取得中（ファイル内進捗は転送完了時に反映）"
                if accelerated
                else f"{target.name} を取得中"
            ),
        )

    if accelerated:
        _download_huggingface(
            str(definition["repo_id"]),
            str(definition["revision"]),
            remote_path,
            str(definition["relative_path"]),
            target,
            expected_size,
            progress,
        )
        downloaded_path = target
    else:
        _download_stream(url, partial, expected_size, progress)
        downloaded_path = partial
    _set_state(status="verifying", message=f"{target.name} の安全確認中")
    if _sha256(downloaded_path, file_key, completed_before, total_size) != definition["sha256"]:
        downloaded_path.rename(downloaded_path.with_suffix(downloaded_path.suffix + f".invalid.{int(time.time())}"))
        raise RuntimeError(f"SHA-256が一致しません: {target.name}")
    if downloaded_path != target:
        os.replace(downloaded_path, target)
    _save_verified(file_key, target)


def _download_package(package_key: str) -> None:
    global DOWNLOAD_THREAD
    file_keys = tuple(MODEL_PACKAGES[package_key]["file_keys"])
    total_size = sum(int(MODEL_FILES[key]["size"]) for key in file_keys)
    completed = 0
    try:
        for index, file_key in enumerate(file_keys, start=1):
            if CANCEL_EVENT.is_set():
                raise InterruptedError("取得を中断しました")
            _prepare_file(file_key, completed, total_size, index, len(file_keys))
            completed += int(MODEL_FILES[file_key]["size"])
        _set_state(
            status="complete",
            total_downloaded=total_size,
            percent=100.0,
            message=f"{MODEL_PACKAGES[package_key]['label']} の準備が完了しました",
            error=None,
            finished_at=time.time(),
        )
    except InterruptedError as exc:
        _set_state(
            status="canceled",
            message="取得を中断しました。再開ボタンで続きから取得できます",
            error=str(exc),
            finished_at=time.time(),
        )
    except Exception as exc:
        _set_state(
            status="error",
            message="モデルの準備に失敗しました",
            error=str(exc)[:500],
            finished_at=time.time(),
        )
    finally:
        with STATE_LOCK:
            DOWNLOAD_THREAD = None


def start_install(package_key: str) -> dict[str, Any]:
    global DOWNLOAD_THREAD
    if DISABLE_MODEL_DOWNLOAD:
        raise RuntimeError("この環境ではモデル取得を無効にしています")
    if package_key not in MODEL_PACKAGES:
        raise ValueError("不正なモデルセットです")
    with STATE_LOCK:
        if DOWNLOAD_THREAD and DOWNLOAD_THREAD.is_alive():
            raise RuntimeError("別のモデルを準備中です")
    package_files = tuple(MODEL_PACKAGES[package_key]["file_keys"])
    total_size = sum(int(MODEL_FILES[key]["size"]) for key in package_files)
    needed = 0
    for key in package_files:
        target = _target(key)
        partial = target.with_suffix(target.suffix + ".part")
        expected = int(MODEL_FILES[key]["size"])
        if target.is_file() and target.stat().st_size == expected:
            continue
        partial_size = min(partial.stat().st_size, expected) if partial.is_file() else 0
        needed += expected - partial_size
    if shutil.disk_usage(MODEL_ROOT).free < needed + 3 * 1024**3:
        shortfall = needed + 3 * 1024**3 - shutil.disk_usage(MODEL_ROOT).free
        required_gb = max(1, (shortfall + 1024**3 - 1) // 1024**3)
        raise RuntimeError(f"空き容量が不足しています。少なくとも約{required_gb}GB追加してください")
    CANCEL_EVENT.clear()
    next_state = _default_state()
    next_state.update(
        status="starting",
        package=package_key,
        file_count=len(package_files),
        total_size=total_size,
        message=f"{MODEL_PACKAGES[package_key]['label']} の準備を開始します",
        started_at=time.time(),
    )
    _set_state(**next_state)
    thread = threading.Thread(target=_download_package, args=(package_key,), daemon=True)
    with STATE_LOCK:
        DOWNLOAD_THREAD = thread
    thread.start()
    return public_status()


def cancel_install() -> dict[str, Any]:
    with STATE_LOCK:
        active = DOWNLOAD_THREAD and DOWNLOAD_THREAD.is_alive()
    if not active:
        raise RuntimeError("現在ダウンロード中ではありません")
    CANCEL_EVENT.set()
    _set_state(message="中断処理中です")
    return public_status()
