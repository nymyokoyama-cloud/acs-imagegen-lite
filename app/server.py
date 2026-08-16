from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import shutil
import sqlite3
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse

from .config import (
    ACTIVITY_FILE,
    APP_DIR,
    APP_NAME,
    COMFY_URL,
    COMFY_INPUT_DIR,
    COOKIE_SECURE,
    DATA_DIR,
    DB_PATH,
    DISABLE_WORKER,
    JOB_TIMEOUT_SEC,
    H3_ACCEPTANCE_FILE,
    H3_ACCEPTANCE_LOG_FILE,
    H3_ENFORCEMENT_PATH,
    H3_LICENSE_PATH,
    H3_LICENSE_SHA256,
    H3_LICENSE_URL,
    H3_LICENSE_VERSION,
    H3_MODEL_KEY,
    H3_REPORT_URL,
    H3_SAFETY_LOG_FILE,
    H3_SIZES,
    H3_TERMS_PATH,
    H3_TERMS_VERSION,
    KREA_ACCEPTANCE_FILE,
    KREA_ACCEPTANCE_LOG_FILE,
    KREA_AUP_URL,
    KREA_LICENSE_SHA256,
    KREA_LICENSE_URL,
    KREA_LICENSE_VERSION,
    KREA_SAFETY_LOG_FILE,
    KREA_TERMS_PATH,
    KREA_TERMS_VERSION,
    LORA_DIR,
    MAX_INPUT_IMAGE_BYTES,
    MAX_LORA_BYTES,
    MAX_PROMPT_LENGTH,
    MODEL_DEFINITIONS,
    OUTPUT_DIR,
    PASSWORD_FILE,
    POD_ACTION_STATE_FILE,
    SESSION_KEY_FILE,
    SIZES,
    STYLES,
    VERSION,
    ZIMAGE_LICENSE_NAME,
    ZIMAGE_LICENSE_PATH,
    ZIMAGE_LICENSE_URL,
    ZIMAGE_MODEL_NAME,
    ZIMAGE_REPACK_REPO,
    ZIMAGE_SAFETY_LOG_FILE,
    ZIMAGE_TERMS_PATH,
    ZIMAGE_TERMS_VERSION,
    ZIMAGE_UPSTREAM_REPO,
    ensure_directories,
    h3_available,
    h3_region_status,
    model_available,
    model_engine,
    zimage_available,
)
from .workflow import build_h3_workflow, build_workflow
from .model_manager import cancel_install, public_status as model_public_status, start_install
from .config import MODEL_PACKAGES
from .h3_safety import blocked_h3_categories, blocked_krea_categories, blocked_zimage_categories


HTML_PATH = APP_DIR / "templates" / "index.html"
PASSWORD_MIN_LENGTH = 10
SESSION_MAX_AGE = 12 * 60 * 60
PASSWORD_ITERATIONS = 600_000
SAFE_LORA_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")
VIDEO_MODES = {"t2v", "i2v", "flf"}
MEDIA_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".webm"}
H3_CONFIRMATION_KEYS = (
    "territory",
    "license",
    "aup",
    "rights",
    "disclosure",
    "no_other_ai_training",
    "reporting",
)
KREA_CONFIRMATION_KEYS = (
    "license",
    "revenue",
    "aup",
    "rights",
    "filtering_and_review",
)
LOGIN_FAILURES: dict[str, list[float]] = {}
LOGIN_WINDOW_SECONDS = 5 * 60
LOGIN_MAX_FAILURES = 8
H3_ACCEPTANCE_LOCK = threading.Lock()
H3_SAFETY_LOG_LOCK = threading.Lock()
KREA_ACCEPTANCE_LOCK = threading.Lock()
KREA_SAFETY_LOG_LOCK = threading.Lock()
ZIMAGE_SAFETY_LOG_LOCK = threading.Lock()
POD_ACTION_LOCK = threading.Lock()


ensure_directories()


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL,
            created_at REAL NOT NULL,
            started_at REAL,
            finished_at REAL,
            model_key TEXT NOT NULL,
            prompt TEXT NOT NULL,
            negative TEXT NOT NULL DEFAULT '',
            ratio TEXT NOT NULL,
            style_key TEXT NOT NULL,
            seed INTEGER NOT NULL,
            lora_name TEXT,
            lora_strength REAL NOT NULL DEFAULT 1.0,
            trigger_word TEXT NOT NULL DEFAULT '',
            output_name TEXT,
            error TEXT
        )
        """
    )
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(jobs)").fetchall()}
    migrations = {
        "job_kind": "TEXT NOT NULL DEFAULT 'image'",
        "video_mode": "TEXT",
        "duration": "REAL",
        "first_frame_name": "TEXT",
        "last_frame_name": "TEXT",
    }
    for name, declaration in migrations.items():
        if name not in columns:
            conn.execute(f"ALTER TABLE jobs ADD COLUMN {name} {declaration}")
    conn.commit()
    return conn


with db() as _initial_db:
    _interrupted_jobs = _initial_db.execute("SELECT * FROM jobs WHERE status='running'").fetchall()
    _initial_db.execute("UPDATE jobs SET status='error', error='server restarted' WHERE status='running'")
    _initial_db.commit()
for _interrupted_job in _interrupted_jobs:
    _cleanup_values = {
        "first_frame_name": _interrupted_job["first_frame_name"],
        "last_frame_name": _interrupted_job["last_frame_name"],
    }
    for _cleanup_name in _cleanup_values.values():
        if _cleanup_name:
            (COMFY_INPUT_DIR / Path(str(_cleanup_name)).name).unlink(missing_ok=True)


def touch_activity() -> None:
    ACTIVITY_FILE.touch(exist_ok=True)


def _pod_api_key() -> str:
    return os.environ.get("ACS_RUNPOD_API_KEY", "") or os.environ.get("RUNPOD_API_KEY", "")


def _read_pod_action_state() -> dict[str, Any]:
    try:
        value = json.loads(POD_ACTION_STATE_FILE.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def _write_pod_action_state(**values: Any) -> dict[str, Any]:
    with POD_ACTION_LOCK:
        state = _read_pod_action_state()
        state.update(values)
        temporary = POD_ACTION_STATE_FILE.with_name(
            f".{POD_ACTION_STATE_FILE.name}.{os.getpid()}.{threading.get_ident()}.tmp"
        )
        temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        os.chmod(temporary, 0o600)
        temporary.replace(POD_ACTION_STATE_FILE)
        return state


def _password_record(password: str) -> dict[str, str | int]:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS, dklen=32
    )
    return {
        "version": 1,
        "algorithm": "pbkdf2-sha256",
        "iterations": PASSWORD_ITERATIONS,
        "salt": salt.hex(),
        "digest": digest.hex(),
    }


def _write_password(password: str) -> None:
    record = _password_record(password)
    PASSWORD_FILE.write_text(json.dumps(record), encoding="utf-8")
    PASSWORD_FILE.chmod(0o600)


def password_configured() -> bool:
    return PASSWORD_FILE.is_file()


def check_password(password: str) -> bool:
    try:
        record = json.loads(PASSWORD_FILE.read_text(encoding="utf-8"))
        if record.get("algorithm") != "pbkdf2-sha256":
            return False
        salt = bytes.fromhex(record["salt"])
        wanted = bytes.fromhex(record["digest"])
        iterations = int(record["iterations"])
        if not 100_000 <= iterations <= 2_000_000:
            return False
        got = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, iterations, dklen=32
        )
        return hmac.compare_digest(wanted, got)
    except Exception:
        return False


def initialize_password_from_env() -> None:
    password = os.environ.get("ACS_WEB_PASSWORD", "")
    if password and not password_configured():
        if len(password) < PASSWORD_MIN_LENGTH:
            raise RuntimeError(f"ACS_WEB_PASSWORD must be at least {PASSWORD_MIN_LENGTH} characters")
        _write_password(password)


def session_key() -> bytes:
    if not SESSION_KEY_FILE.exists():
        SESSION_KEY_FILE.write_bytes(secrets.token_bytes(32))
        SESSION_KEY_FILE.chmod(0o600)
    return SESSION_KEY_FILE.read_bytes()


def make_token() -> str:
    timestamp = str(int(time.time()))
    signature = hmac.new(session_key(), timestamp.encode(), hashlib.sha256).hexdigest()
    return f"{timestamp}.{signature}"


def check_token(token: str) -> bool:
    try:
        timestamp, signature = token.split(".", 1)
        wanted = hmac.new(session_key(), timestamp.encode(), hashlib.sha256).hexdigest()
        age = time.time() - float(timestamp)
        return 0 <= age < SESSION_MAX_AGE and hmac.compare_digest(signature, wanted)
    except Exception:
        return False


def request_client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def login_blocked(client_key: str) -> bool:
    cutoff = time.time() - LOGIN_WINDOW_SECONDS
    recent = [value for value in LOGIN_FAILURES.get(client_key, []) if value >= cutoff]
    LOGIN_FAILURES[client_key] = recent
    return len(recent) >= LOGIN_MAX_FAILURES


def record_login_failure(client_key: str) -> None:
    LOGIN_FAILURES.setdefault(client_key, []).append(time.time())


def same_origin(request: Request) -> bool:
    origin = request.headers.get("origin")
    if not origin:
        return True
    parsed = urllib.parse.urlparse(origin)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False

    origin_host = parsed.hostname.lower().rstrip(".")
    request_host = request.headers.get("host", "").strip()
    host_parsed = urllib.parse.urlparse(f"//{request_host}")
    if host_parsed.hostname and origin_host == host_parsed.hostname.lower().rstrip("."):
        return True

    pod_id = os.environ.get("RUNPOD_POD_ID", "").strip().lower()
    if re.fullmatch(r"[a-z0-9-]{1,64}", pod_id):
        return origin_host == f"{pod_id}-8080.proxy.runpod.net"
    return False


initialize_password_from_env()


def comfy_alive() -> bool:
    try:
        with urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=3):  # nosec B310
            return True
    except Exception:
        return False


def safe_lora_name(name: str) -> str:
    clean = Path(name).name
    if not clean.endswith(".safetensors"):
        raise ValueError("LoRAは.safetensors形式だけアップロードできます")
    if not clean or any(char not in SAFE_LORA_CHARS for char in clean):
        raise ValueError("ファイル名は半角英数字、ハイフン、アンダースコア、ドットだけにしてください")
    return clean


def krea_acceptance() -> dict[str, Any] | None:
    try:
        record = json.loads(KREA_ACCEPTANCE_FILE.read_text(encoding="utf-8"))
        confirmations = record.get("confirmations", {})
        if (
            record.get("license_version") == KREA_LICENSE_VERSION
            and record.get("license_sha256") == KREA_LICENSE_SHA256
            and record.get("terms_version") == KREA_TERMS_VERSION
            and record.get("accepted") is True
            and all(confirmations.get(key) is True for key in KREA_CONFIRMATION_KEYS)
        ):
            return record
    except Exception:  # nosec B110
        pass
    return None


def log_krea_safety_block(categories: list[str], stage: str) -> None:
    record = {
        "blocked_at": datetime.now(timezone.utc).isoformat(),
        "app_version": VERSION,
        "stage": stage,
        "categories": sorted(set(categories)),
    }
    try:
        with KREA_SAFETY_LOG_LOCK:
            with KREA_SAFETY_LOG_FILE.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            KREA_SAFETY_LOG_FILE.chmod(0o600)
    except OSError:
        pass


def krea_ready_for_access() -> tuple[bool, str]:
    if not krea_acceptance():
        return False, "Krea 2の公式ライセンスと利用条件への同意が必要です"
    return True, "利用できます"


def log_zimage_safety_block(categories: list[str], stage: str) -> None:
    record = {
        "blocked_at": datetime.now(timezone.utc).isoformat(),
        "app_version": VERSION,
        "stage": stage,
        "categories": sorted(set(categories)),
    }
    try:
        with ZIMAGE_SAFETY_LOG_LOCK:
            with ZIMAGE_SAFETY_LOG_FILE.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            ZIMAGE_SAFETY_LOG_FILE.chmod(0o600)
    except OSError:
        pass


def zimage_ready_for_access() -> tuple[bool, str]:
    """Z-Image TurboはApache-2.0で追加の同意条件がないため、同意ゲートを設けない。"""
    return True, "利用できます"


def image_engine_ready(model_key: str) -> tuple[bool, str]:
    if model_engine(model_key) == "zimage":
        return zimage_ready_for_access()
    return krea_ready_for_access()


def blocked_image_categories(model_key: str, prompt: str) -> list[str]:
    if model_engine(model_key) == "zimage":
        return blocked_zimage_categories(prompt)
    return blocked_krea_categories(prompt)


def log_image_safety_block(model_key: str, categories: list[str], stage: str) -> None:
    if model_engine(model_key) == "zimage":
        log_zimage_safety_block(categories, stage)
    else:
        log_krea_safety_block(categories, stage)


def image_safety_report_url(model_key: str) -> str:
    if model_engine(model_key) == "zimage":
        return ZIMAGE_UPSTREAM_REPO
    return KREA_AUP_URL


def h3_acceptance() -> dict[str, Any] | None:
    if not h3_license_integrity_ok():
        return None
    try:
        record = json.loads(H3_ACCEPTANCE_FILE.read_text(encoding="utf-8"))
        confirmations = record.get("confirmations", {})
        if (
            record.get("license_version") == H3_LICENSE_VERSION
            and record.get("license_sha256") == H3_LICENSE_SHA256
            and record.get("terms_version") == H3_TERMS_VERSION
            and record.get("accepted") is True
            and all(confirmations.get(key) is True for key in H3_CONFIRMATION_KEYS)
        ):
            return record
    except Exception:  # nosec B110
        pass
    return None


def h3_license_integrity_ok() -> bool:
    try:
        digest = hashlib.sha256(H3_LICENSE_PATH.read_bytes()).hexdigest()
        return hmac.compare_digest(digest, H3_LICENSE_SHA256)
    except OSError:
        return False


def log_h3_safety_block(categories: list[str], stage: str) -> None:
    record = {
        "blocked_at": datetime.now(timezone.utc).isoformat(),
        "app_version": VERSION,
        "stage": stage,
        "categories": sorted(set(categories)),
    }
    try:
        with H3_SAFETY_LOG_LOCK:
            with H3_SAFETY_LOG_FILE.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            H3_SAFETY_LOG_FILE.chmod(0o600)
    except OSError:
        # 監査ログ障害があっても、安全側の生成拒否は継続する。
        pass


def h3_ready_for_access() -> tuple[bool, str]:
    region = h3_region_status()
    if not region["allowed"]:
        return False, str(region["reason"])
    if not h3_license_integrity_ok():
        return False, "同梱MiniMax H3ライセンスの完全性を確認できません"
    if not h3_acceptance():
        return False, "MiniMax H3の利用条件への同意が必要です"
    return True, "利用できます"


def _image_suffix(header: bytes) -> str | None:
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if header.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return ".webp"
    return None


async def save_input_image(file: Optional[UploadFile], label: str) -> Optional[str]:
    if file is None or not file.filename:
        return None
    temporary = COMFY_INPUT_DIR / f".{secrets.token_hex(16)}.uploading"
    total = 0
    header = b""
    try:
        with temporary.open("xb") as handle:
            while chunk := await file.read(1024 * 1024):
                if not header:
                    header = chunk[:16]
                total += len(chunk)
                if total > MAX_INPUT_IMAGE_BYTES:
                    raise ValueError(f"{label}は{MAX_INPUT_IMAGE_BYTES // 1024**2}MB以下にしてください")
                handle.write(chunk)
        suffix = _image_suffix(header)
        if not suffix:
            raise ValueError(f"{label}はPNG・JPEG・WebPだけ使用できます")
        destination = COMFY_INPUT_DIR / f"h3-{secrets.token_hex(16)}{suffix}"
        temporary.replace(destination)
        return destination.name
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _cleanup_job_inputs(row: sqlite3.Row | dict[str, Any]) -> None:
    for key in ("first_frame_name", "last_frame_name"):
        try:
            value = row[key]
        except (KeyError, IndexError):
            value = None
        if value:
            (COMFY_INPUT_DIR / Path(str(value)).name).unlink(missing_ok=True)


def list_loras() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in sorted(LORA_DIR.glob("*.safetensors"), key=lambda p: p.name.lower()):
        items.append({"name": path.name, "size": path.stat().st_size})
    return items


def queued_count() -> int:
    with db() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM jobs WHERE status IN ('queued','running')").fetchone()
    return int(row["n"])


def cancel_requested(job_id: int) -> bool:
    with db() as conn:
        row = conn.execute("SELECT status FROM jobs WHERE id=?", (job_id,)).fetchone()
    return not row or row["status"] == "canceled"


def _submit_to_comfy(graph: dict[str, Any]) -> str:
    body = json.dumps({"prompt": graph}).encode("utf-8")
    request = urllib.request.Request(
        f"{COMFY_URL}/prompt",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310
        payload = json.load(response)
    prompt_id = payload.get("prompt_id")
    if not prompt_id:
        raise RuntimeError("ComfyUI did not return a prompt id")
    return str(prompt_id)


def _copy_comfy_output(
    history: dict[str, Any],
    prompt_id: str,
    job_id: int,
    *,
    h3_output: bool = False,
    krea_output: bool = False,
    zimage_output: bool = False,
) -> str:
    outputs = history.get(prompt_id, {}).get("outputs", {})
    for node in outputs.values():
        for output_type in ("videos", "gifs", "images"):
            for media in node.get(output_type, []):
                filename = Path(media.get("filename", "")).name
                if not filename:
                    continue
                subfolder = Path(media.get("subfolder", ""))
                if subfolder.is_absolute() or ".." in subfolder.parts:
                    continue
                source_root = Path(os.environ.get("ACS_COMFY_OUTPUT_DIR", "/workspace/comfy-output"))
                source = source_root / subfolder / filename
                if not source.is_file() or source.suffix.lower() not in MEDIA_SUFFIXES:
                    continue
                marker = (
                    "-minimax-h3-ai"
                    if h3_output
                    else "-krea2-ai"
                    if krea_output
                    else "-zimage-ai"
                    if zimage_output
                    else ""
                )
                destination = OUTPUT_DIR / f"job-{job_id}{marker}{source.suffix.lower()}"
                shutil.copy2(source, destination)
                return destination.name
    raise RuntimeError("ComfyUI output file was not found")


def run_job(row: sqlite3.Row) -> str:
    if not comfy_alive():
        raise RuntimeError("ComfyUI is not ready")
    if row["job_kind"] == "video":
        allowed, reason = h3_ready_for_access()
        if not allowed:
            raise RuntimeError(reason)
        blocked = blocked_h3_categories(str(row["prompt"]))
        if blocked:
            log_h3_safety_block(blocked, "worker")
            raise RuntimeError("MiniMax H3安全フィルターにより生成を拒否しました")
        if not h3_available():
            raise RuntimeError("MiniMax H3 model is not installed")
        ratio = row["ratio"]
        if ratio not in H3_SIZES:
            raise RuntimeError("invalid H3 ratio")
        width, height = H3_SIZES[ratio]
        graph = build_h3_workflow(
            mode=row["video_mode"],
            prompt=row["prompt"],
            width=width,
            height=height,
            seconds=float(row["duration"]),
            seed=int(row["seed"]),
            first_frame=row["first_frame_name"],
            last_frame=row["last_frame_name"],
        )
        return _wait_for_comfy(_submit_to_comfy(graph), int(row["id"]), h3_output=True)

    model_key = row["model_key"]
    engine = model_engine(model_key)
    allowed, reason = image_engine_ready(model_key)
    if not allowed:
        raise RuntimeError(reason)
    blocked = blocked_image_categories(model_key, str(row["prompt"]))
    if blocked:
        log_image_safety_block(model_key, blocked, "worker")
        raise RuntimeError(
            "Z-Image安全フィルターにより生成を拒否しました"
            if engine == "zimage"
            else "Krea 2安全フィルターにより生成を拒否しました"
        )
    if not model_available(model_key):
        raise RuntimeError(f"model is not installed: {model_key}")
    ratio = row["ratio"]
    if ratio not in SIZES:
        raise RuntimeError("invalid ratio")
    width, height = SIZES[ratio]
    lora_name = row["lora_name"]
    if lora_name and not (LORA_DIR / safe_lora_name(lora_name)).is_file():
        raise RuntimeError("selected LoRA is not installed")
    graph = build_workflow(
        model_key=model_key,
        prompt=row["prompt"],
        negative=row["negative"],
        width=width,
        height=height,
        seed=int(row["seed"]),
        lora_name=lora_name,
        lora_strength=float(row["lora_strength"]),
        trigger_word=row["trigger_word"],
        style_key=row["style_key"],
    )
    return _wait_for_comfy(
        _submit_to_comfy(graph),
        int(row["id"]),
        krea_output=engine == "krea2",
        zimage_output=engine == "zimage",
    )


def _wait_for_comfy(
    prompt_id: str,
    job_id: int,
    *,
    h3_output: bool = False,
    krea_output: bool = False,
    zimage_output: bool = False,
) -> str:
    deadline = time.time() + JOB_TIMEOUT_SEC
    while time.time() < deadline:
        if cancel_requested(job_id):
            try:
                urllib.request.urlopen(  # nosec B310
                    urllib.request.Request(f"{COMFY_URL}/interrupt", data=b"", method="POST"),
                    timeout=10,
                )
            except Exception:  # nosec B110
                pass
            raise RuntimeError("canceled")
        try:
            with urllib.request.urlopen(  # nosec B310
                f"{COMFY_URL}/history/{prompt_id}", timeout=10
            ) as response:
                history = json.load(response)
            if prompt_id in history:
                return _copy_comfy_output(
                    history,
                    prompt_id,
                    job_id,
                    h3_output=h3_output,
                    krea_output=krea_output,
                    zimage_output=zimage_output,
                )
        except urllib.error.URLError:
            pass
        time.sleep(2)
    raise RuntimeError("generation timed out")


def worker_loop() -> None:
    while True:
        with db() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY id LIMIT 1").fetchone()
            if row:
                conn.execute(
                    "UPDATE jobs SET status='running', started_at=? WHERE id=? AND status='queued'",
                    (time.time(), row["id"]),
                )
                conn.commit()
                row = conn.execute("SELECT * FROM jobs WHERE id=?", (row["id"],)).fetchone()
        if not row:
            time.sleep(1)
            continue
        try:
            output_name = run_job(row)
            with db() as conn:
                conn.execute(
                    "UPDATE jobs SET status='done', output_name=?, finished_at=? WHERE id=?",
                    (output_name, time.time(), row["id"]),
                )
                conn.commit()
        except Exception as exc:
            status = "canceled" if str(exc) == "canceled" else "error"
            with db() as conn:
                conn.execute(
                    "UPDATE jobs SET status=?, error=?, finished_at=? WHERE id=?",
                    (status, str(exc)[:500], time.time(), row["id"]),
                )
                conn.commit()
        finally:
            _cleanup_job_inputs(row)


def public_job(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "status": row["status"],
        "created_at": row["created_at"],
        "started_at": row["started_at"],
        "finished_at": row["finished_at"],
        "model_key": row["model_key"],
        "job_kind": row["job_kind"],
        "video_mode": row["video_mode"],
        "duration": row["duration"],
        "prompt": row["prompt"],
        "ratio": row["ratio"],
        "seed": row["seed"],
        "lora_name": row["lora_name"],
        "output_name": row["output_name"],
        "error": row["error"],
    }


def setup_page(message: str = "") -> str:
    warning = f"<p class='error'>{message}</p>" if message else ""
    return f"""<!doctype html><html lang='ja'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>{APP_NAME} 初回設定</title><style>body{{background:#07111f;color:#ecf4ff;font-family:system-ui;margin:0}}main{{max-width:480px;margin:12vh auto;padding:32px;background:#101e31;border:1px solid #29415f;border-radius:18px}}input,button{{box-sizing:border-box;width:100%;font-size:16px;padding:13px;margin-top:12px;border-radius:10px}}button{{background:#55a6ff;border:0;font-weight:800;color:#06101d}}.error{{color:#ff9a9a}}small{{color:#a9bed8}}</style><main>
<h1>{APP_NAME}</h1><h2>初回パスワード設定</h2>{warning}<p>このRunPod環境を保護するパスワードを設定してください。</p>
<form method='post' action='/api/setup'><input type='password' name='password' minlength='{PASSWORD_MIN_LENGTH}' autocomplete='new-password' placeholder='{PASSWORD_MIN_LENGTH}文字以上' required><input type='password' name='confirm' minlength='{PASSWORD_MIN_LENGTH}' autocomplete='new-password' placeholder='確認用' required><button>設定して開始</button></form>
<p><small>パスワードはハッシュ化してこのPodのデータ領域へ保存します。</small></p></main></html>"""


def login_page(message: str = "") -> str:
    warning = f"<p class='error'>{message}</p>" if message else ""
    return f"""<!doctype html><html lang='ja'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>{APP_NAME} ログイン</title><style>body{{background:#07111f;color:#ecf4ff;font-family:system-ui;margin:0}}main{{max-width:420px;margin:15vh auto;padding:32px;background:#101e31;border:1px solid #29415f;border-radius:18px}}input,button{{box-sizing:border-box;width:100%;font-size:16px;padding:13px;margin-top:12px;border-radius:10px}}button{{background:#55a6ff;border:0;font-weight:800;color:#06101d}}.error{{color:#ff9a9a}}</style><main>
<h1>{APP_NAME}</h1>{warning}<form method='post' action='/api/login'><input type='password' name='password' autocomplete='current-password' placeholder='パスワード' required><button>ログイン</button></form></main></html>"""


app = FastAPI(title=APP_NAME, version=VERSION)


@app.middleware("http")
async def authentication(request: Request, call_next):
    path = request.url.path
    public_paths = {
        "/setup",
        "/api/setup",
        "/login",
        "/api/login",
        "/healthz",
        "/legal/minimax-h3-license",
        "/legal/krea2-terms",
        "/legal/h3-terms",
        "/legal/h3-enforcement",
        "/legal/z-image-license",
        "/legal/z-image-terms",
    }
    if request.method not in {"GET", "HEAD", "OPTIONS"} and not same_origin(request):
        return JSONResponse({"error": "origin check failed"}, status_code=403)
    if path in public_paths:
        return await call_next(request)
    if not password_configured():
        if path.startswith("/api/"):
            return JSONResponse({"error": "setup required"}, status_code=428)
        return RedirectResponse("/setup", status_code=303)
    if not check_token(request.cookies.get("acs_lite_session", "")):
        if path.startswith("/api/"):
            return JSONResponse({"error": "authentication required"}, status_code=401)
        return RedirectResponse("/login", status_code=303)
    return await call_next(request)


@app.get("/healthz")
def healthz():
    return {"ok": True, "version": VERSION}


@app.get("/legal/minimax-h3-license", response_class=PlainTextResponse)
def minimax_h3_license():
    return PlainTextResponse(H3_LICENSE_PATH.read_text(encoding="utf-8"))


@app.get("/legal/krea2-terms", response_class=PlainTextResponse)
def krea2_terms():
    return PlainTextResponse(KREA_TERMS_PATH.read_text(encoding="utf-8"))


@app.get("/legal/h3-terms", response_class=PlainTextResponse)
def h3_terms():
    return PlainTextResponse(H3_TERMS_PATH.read_text(encoding="utf-8"))


@app.get("/legal/h3-enforcement", response_class=PlainTextResponse)
def h3_enforcement():
    return PlainTextResponse(H3_ENFORCEMENT_PATH.read_text(encoding="utf-8"))


@app.get("/legal/z-image-license", response_class=PlainTextResponse)
def z_image_license():
    return PlainTextResponse(ZIMAGE_LICENSE_PATH.read_text(encoding="utf-8"))


@app.get("/legal/z-image-terms", response_class=PlainTextResponse)
def z_image_terms():
    return PlainTextResponse(ZIMAGE_TERMS_PATH.read_text(encoding="utf-8"))


@app.get("/setup", response_class=HTMLResponse)
def get_setup():
    if password_configured():
        return RedirectResponse("/login", status_code=303)
    return HTMLResponse(setup_page())


@app.post("/api/setup")
def post_setup(password: str = Form(...), confirm: str = Form(...)):
    if password_configured():
        return JSONResponse({"error": "setup already completed"}, status_code=409)
    if password != confirm:
        return HTMLResponse(setup_page("確認用パスワードが一致しません"), status_code=400)
    if len(password) < PASSWORD_MIN_LENGTH:
        return HTMLResponse(setup_page(f"パスワードは{PASSWORD_MIN_LENGTH}文字以上にしてください"), status_code=400)
    _write_password(password)
    touch_activity()
    return RedirectResponse("/login", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def get_login():
    if not password_configured():
        return RedirectResponse("/setup", status_code=303)
    return HTMLResponse(login_page())


@app.post("/api/login")
def post_login(request: Request, password: str = Form(...)):
    client_key = request_client_key(request)
    if login_blocked(client_key):
        return HTMLResponse(login_page("試行回数が多すぎます。5分後に再度お試しください"), status_code=429)
    if not check_password(password):
        record_login_failure(client_key)
        return HTMLResponse(login_page("パスワードが違います"), status_code=401)
    LOGIN_FAILURES.pop(client_key, None)
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        "acs_lite_session",
        make_token(),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
    )
    touch_activity()
    return response


@app.get("/", response_class=HTMLResponse)
def index():
    touch_activity()
    return HTMLResponse(HTML_PATH.read_text(encoding="utf-8"))


@app.get("/api/config")
def api_config():
    return {
        "app": APP_NAME,
        "version": VERSION,
        "models": [
            {
                "key": key,
                "label": value["label"],
                "engine": model_engine(key),
                "unet": value["unet"],
                "available": model_available(key),
                "negative": value["negative"],
            }
            for key, value in MODEL_DEFINITIONS.items()
        ],
        "ratios": list(SIZES.keys()),
        "h3_ratios": list(H3_SIZES.keys()),
        "h3_available": h3_available(),
        "zimage_available": zimage_available(),
        "styles": [{"key": key, "label": value[0]} for key, value in STYLES.items()],
        "loras": list_loras(),
        "pod_default_action": "terminate",
        "pod_api_ready": bool(os.environ.get("RUNPOD_POD_ID") and _pod_api_key()),
        "storage_mode": "network" if os.environ.get("RUNPOD_VOLUME_ID") else "temporary",
    }


@app.get("/api/models")
def api_models():
    result = model_public_status()
    result["krea"] = api_krea_status()
    result["h3"] = api_h3_status()
    result["zimage"] = api_zimage_status()
    return result


@app.get("/api/zimage/status")
def api_zimage_status():
    # Apache-2.0のため同意ゲートは存在しない。表示・出典・安全検査だけを提供する。
    return {
        "model_name": ZIMAGE_MODEL_NAME,
        "available": zimage_available(),
        "license_name": ZIMAGE_LICENSE_NAME,
        "license_url": ZIMAGE_LICENSE_URL,
        "license_local_url": "/legal/z-image-license",
        "terms_url": "/legal/z-image-terms",
        "terms_version": ZIMAGE_TERMS_VERSION,
        "upstream_repo": ZIMAGE_UPSTREAM_REPO,
        "repack_repo": ZIMAGE_REPACK_REPO,
        "acceptance_required": False,
        "safety_filter": True,
        "human_output_review_required": True,
    }


@app.get("/api/krea/status")
def api_krea_status():
    accepted = krea_acceptance()
    return {
        "model_name": "Krea 2",
        "accepted": bool(accepted),
        "accepted_at": accepted.get("accepted_at") if accepted else None,
        "license_version": KREA_LICENSE_VERSION,
        "license_sha256": KREA_LICENSE_SHA256,
        "license_url": KREA_LICENSE_URL,
        "aup_url": KREA_AUP_URL,
        "terms_version": KREA_TERMS_VERSION,
        "terms_url": "/legal/krea2-terms",
        "safety_filter": True,
        "human_output_review_required": True,
    }


@app.post("/api/krea/accept")
def api_krea_accept(
    license_confirm: str = Form(...),
    revenue_confirm: str = Form(...),
    aup_confirm: str = Form(...),
    rights_confirm: str = Form(...),
    filtering_confirm: str = Form(...),
):
    submitted = (
        license_confirm,
        revenue_confirm,
        aup_confirm,
        rights_confirm,
        filtering_confirm,
    )
    if any(value != "yes" for value in submitted):
        return JSONResponse({"error": "5項目すべてへの同意が必要です"}, status_code=400)
    accepted_at = datetime.now(timezone.utc).isoformat()
    record = {
        "accepted": True,
        "acceptance_id": secrets.token_hex(16),
        "accepted_at": accepted_at,
        "accepted_at_epoch": time.time(),
        "app_version": VERSION,
        "license_version": KREA_LICENSE_VERSION,
        "license_sha256": KREA_LICENSE_SHA256,
        "terms_version": KREA_TERMS_VERSION,
        "aup_url": KREA_AUP_URL,
        "confirmations": {key: True for key in KREA_CONFIRMATION_KEYS},
    }
    with KREA_ACCEPTANCE_LOCK:
        with KREA_ACCEPTANCE_LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        KREA_ACCEPTANCE_LOG_FILE.chmod(0o600)
        temporary = KREA_ACCEPTANCE_FILE.with_name(
            f".{KREA_ACCEPTANCE_FILE.name}.{secrets.token_hex(8)}.tmp"
        )
        temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.chmod(0o600)
        temporary.replace(KREA_ACCEPTANCE_FILE)
        KREA_ACCEPTANCE_FILE.chmod(0o600)
    touch_activity()
    return api_krea_status()


@app.get("/api/h3/status")
def api_h3_status():
    region = h3_region_status()
    accepted = h3_acceptance()
    return {
        "model_name": "MiniMax H3",
        "available": h3_available(),
        "accepted": bool(accepted),
        "accepted_at": accepted.get("accepted_at") if accepted else None,
        "license_version": H3_LICENSE_VERSION,
        "license_sha256": H3_LICENSE_SHA256,
        "terms_version": H3_TERMS_VERSION,
        "license_url": H3_LICENSE_URL,
        "license_local_url": "/legal/minimax-h3-license",
        "license_integrity_ok": h3_license_integrity_ok(),
        "terms_url": "/legal/h3-terms",
        "enforcement_url": "/legal/h3-enforcement",
        "report_url": H3_REPORT_URL,
        "safety_filter": True,
        "region": region,
    }


@app.post("/api/h3/accept")
def api_h3_accept(
    territory_confirm: str = Form(...),
    license_confirm: str = Form(...),
    aup_confirm: str = Form(...),
    rights_confirm: str = Form(...),
    disclosure_confirm: str = Form(...),
    no_training_confirm: str = Form(...),
    reporting_confirm: str = Form(...),
):
    region = h3_region_status()
    if not region["allowed"]:
        return JSONResponse({"error": str(region["reason"])}, status_code=451)
    if not h3_license_integrity_ok():
        return JSONResponse(
            {"error": "同梱MiniMax H3ライセンスの完全性を確認できません"},
            status_code=503,
        )
    submitted = (
        territory_confirm,
        license_confirm,
        aup_confirm,
        rights_confirm,
        disclosure_confirm,
        no_training_confirm,
        reporting_confirm,
    )
    if any(value != "yes" for value in submitted):
        return JSONResponse({"error": "7項目すべてへの同意が必要です"}, status_code=400)
    accepted_at = datetime.now(timezone.utc).isoformat()
    record = {
        "accepted": True,
        "acceptance_id": secrets.token_hex(16),
        "accepted_at": accepted_at,
        "accepted_at_epoch": time.time(),
        "app_version": VERSION,
        "license_version": H3_LICENSE_VERSION,
        "license_sha256": H3_LICENSE_SHA256,
        "terms_version": H3_TERMS_VERSION,
        "runpod_dc_id": region["dc_id"],
        "report_url": H3_REPORT_URL,
        "confirmations": {key: True for key in H3_CONFIRMATION_KEYS},
    }
    with H3_ACCEPTANCE_LOCK:
        with H3_ACCEPTANCE_LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        H3_ACCEPTANCE_LOG_FILE.chmod(0o600)
        temporary = H3_ACCEPTANCE_FILE.with_name(
            f".{H3_ACCEPTANCE_FILE.name}.{secrets.token_hex(8)}.tmp"
        )
        temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.chmod(0o600)
        temporary.replace(H3_ACCEPTANCE_FILE)
        H3_ACCEPTANCE_FILE.chmod(0o600)
    touch_activity()
    return api_h3_status()


@app.post("/api/models/install/{package_key}")
def api_models_install(package_key: str):
    package = MODEL_PACKAGES.get(package_key)
    if package and package.get("requires_krea_terms"):
        allowed, reason = krea_ready_for_access()
        if not allowed:
            return JSONResponse({"error": reason}, status_code=451)
    if package and package.get("requires_h3_terms"):
        allowed, reason = h3_ready_for_access()
        if not allowed:
            return JSONResponse({"error": reason}, status_code=451)
    try:
        start_install(package_key)
    except (RuntimeError, ValueError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=409)
    touch_activity()
    return api_models()


@app.post("/api/models/cancel")
def api_models_cancel():
    try:
        cancel_install()
    except RuntimeError as exc:
        return JSONResponse({"error": str(exc)}, status_code=409)
    touch_activity()
    return api_models()


@app.get("/api/status")
def api_status():
    with db() as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 20").fetchall()
    return {"comfy": comfy_alive(), "pending": queued_count(), "jobs": [public_job(row) for row in rows]}


@app.post("/api/generate")
def api_generate(
    model_key: str = Form(...),
    prompt: str = Form(...),
    negative: str = Form(""),
    ratio: str = Form("16:9"),
    style_key: str = Form("none"),
    seed: str = Form(""),
    lora_name: str = Form(""),
    lora_strength: float = Form(1.0),
    trigger_word: str = Form(""),
):
    if model_key not in MODEL_DEFINITIONS:
        return JSONResponse({"error": "選択したモデルは利用できません"}, status_code=400)
    allowed, reason = image_engine_ready(model_key)
    if not allowed:
        return JSONResponse({"error": reason}, status_code=451)
    prompt = prompt.strip()
    if not prompt or len(prompt) > MAX_PROMPT_LENGTH:
        return JSONResponse({"error": "プロンプトが空か、長すぎます"}, status_code=400)
    if not model_available(model_key):
        return JSONResponse({"error": "選択したモデルは利用できません"}, status_code=400)
    blocked = blocked_image_categories(model_key, prompt)
    if blocked:
        log_image_safety_block(model_key, blocked, "request")
        return JSONResponse(
            {
                "error": (
                    "Z-Image安全フィルターにより生成を拒否しました。利用条件を確認してください。"
                    if model_engine(model_key) == "zimage"
                    else "Krea 2安全フィルターにより生成を拒否しました。利用条件を確認してください。"
                ),
                "categories": blocked,
                "report_url": image_safety_report_url(model_key),
            },
            status_code=422,
        )
    if ratio not in SIZES or style_key not in STYLES:
        return JSONResponse({"error": "比率またはスタイルが不正です"}, status_code=400)
    if not 0 <= lora_strength <= 2:
        return JSONResponse({"error": "LoRA強度は0〜2の範囲にしてください"}, status_code=400)
    chosen_lora: str | None = None
    if lora_name:
        try:
            chosen_lora = safe_lora_name(lora_name)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        if not (LORA_DIR / chosen_lora).is_file():
            return JSONResponse({"error": "選択したLoRAが見つかりません"}, status_code=400)
    try:
        seed_value = secrets.randbelow(2**32) if not seed.strip() else int(seed)
    except ValueError:
        return JSONResponse({"error": "Seedは整数で入力してください"}, status_code=400)
    if not 0 <= seed_value < 2**64:
        return JSONResponse({"error": "Seedが範囲外です"}, status_code=400)
    with db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO jobs(status,created_at,model_key,prompt,negative,ratio,style_key,seed,lora_name,lora_strength,trigger_word)
            VALUES('queued',?,?,?,?,?,?,?,?,?,?)
            """,
            (time.time(), model_key, prompt, negative[:MAX_PROMPT_LENGTH], ratio, style_key, seed_value, chosen_lora, lora_strength, trigger_word[:200]),
        )
        conn.commit()
        job_id = cursor.lastrowid
    touch_activity()
    return {"ok": True, "job_id": job_id, "seed": seed_value}


@app.post("/api/video/generate")
async def api_video_generate(
    mode: str = Form(...),
    prompt: str = Form(...),
    ratio: str = Form("16:9"),
    duration: float = Form(5.0),
    seed: str = Form(""),
    first_frame: Optional[UploadFile] = None,
    last_frame: Optional[UploadFile] = None,
):
    allowed, reason = h3_ready_for_access()
    if not allowed:
        return JSONResponse({"error": reason}, status_code=451)
    if not h3_available():
        return JSONResponse({"error": "MiniMax H3モデルを先に準備してください"}, status_code=400)
    prompt = prompt.strip()
    if not prompt or len(prompt) > MAX_PROMPT_LENGTH:
        return JSONResponse({"error": "プロンプトが空か、長すぎます"}, status_code=400)
    blocked = blocked_h3_categories(prompt)
    if blocked:
        log_h3_safety_block(blocked, "request")
        return JSONResponse(
            {
                "error": "MiniMax H3安全フィルターにより生成を拒否しました。利用条件を確認してください。",
                "categories": blocked,
                "report_url": H3_REPORT_URL,
            },
            status_code=422,
        )
    if mode not in VIDEO_MODES or ratio not in H3_SIZES:
        return JSONResponse({"error": "動画モードまたは比率が不正です"}, status_code=400)
    if not 3 <= duration <= 10:
        return JSONResponse({"error": "動画の長さは3〜10秒にしてください"}, status_code=400)
    if mode in {"i2v", "flf"} and (first_frame is None or not first_frame.filename):
        return JSONResponse({"error": "開始フレーム画像を選択してください"}, status_code=400)
    if mode == "flf" and (last_frame is None or not last_frame.filename):
        return JSONResponse({"error": "終了フレーム画像を選択してください"}, status_code=400)
    try:
        seed_value = secrets.randbelow(2**32) if not seed.strip() else int(seed)
    except ValueError:
        return JSONResponse({"error": "Seedは整数で入力してください"}, status_code=400)
    if not 0 <= seed_value < 2**64:
        return JSONResponse({"error": "Seedが範囲外です"}, status_code=400)

    first_name: str | None = None
    last_name: str | None = None
    try:
        if mode in {"i2v", "flf"}:
            first_name = await save_input_image(first_frame, "開始フレーム")
        if mode == "flf":
            last_name = await save_input_image(last_frame, "終了フレーム")
        with db() as conn:
            cursor = conn.execute(
                """
                INSERT INTO jobs(
                    status,created_at,model_key,prompt,negative,ratio,style_key,seed,
                    lora_name,lora_strength,trigger_word,job_kind,video_mode,duration,
                    first_frame_name,last_frame_name
                ) VALUES('queued',?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    time.time(), H3_MODEL_KEY, prompt, "", ratio, "none", seed_value,
                    None, 1.0, "", "video", mode, duration, first_name, last_name,
                ),
            )
            conn.commit()
            job_id = cursor.lastrowid
    except (ValueError, OSError, sqlite3.Error) as exc:
        if first_name:
            (COMFY_INPUT_DIR / first_name).unlink(missing_ok=True)
        if last_name:
            (COMFY_INPUT_DIR / last_name).unlink(missing_ok=True)
        return JSONResponse({"error": str(exc)}, status_code=400)
    touch_activity()
    return {"ok": True, "job_id": job_id, "seed": seed_value}


@app.post("/api/jobs/{job_id}/cancel")
def api_cancel(job_id: int):
    with db() as conn:
        row = conn.execute("SELECT status FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            return JSONResponse({"error": "ジョブが見つかりません"}, status_code=404)
        if row["status"] not in {"queued", "running"}:
            return JSONResponse({"error": "このジョブは停止できません"}, status_code=409)
        full_row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        conn.execute("UPDATE jobs SET status='canceled', finished_at=? WHERE id=?", (time.time(), job_id))
        conn.commit()
    if full_row and row["status"] == "queued":
        _cleanup_job_inputs(full_row)
    touch_activity()
    return {"ok": True}


@app.get("/api/images/{name}")
def api_image(name: str):
    clean = Path(name).name
    path = OUTPUT_DIR / clean
    if not path.is_file() or path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        return JSONResponse({"error": "画像が見つかりません"}, status_code=404)
    touch_activity()
    headers = {}
    if "-krea2-ai" in clean:
        headers["X-AI-Generated-By"] = "Krea 2"
    elif "-zimage-ai" in clean:
        headers["X-AI-Generated-By"] = ZIMAGE_MODEL_NAME
    return FileResponse(path, filename=clean, headers=headers)


@app.get("/api/outputs/{name}")
def api_output(name: str):
    clean = Path(name).name
    path = OUTPUT_DIR / clean
    if not path.is_file() or path.suffix.lower() not in MEDIA_SUFFIXES:
        return JSONResponse({"error": "生成ファイルが見つかりません"}, status_code=404)
    touch_activity()
    headers = {}
    if "-minimax-h3-ai" in clean:
        headers["X-AI-Generated-By"] = "MiniMax H3"
    elif "-krea2-ai" in clean:
        headers["X-AI-Generated-By"] = "Krea 2"
    elif "-zimage-ai" in clean:
        headers["X-AI-Generated-By"] = ZIMAGE_MODEL_NAME
    return FileResponse(path, filename=clean, headers=headers)


@app.post("/api/loras")
async def api_upload_lora(file: UploadFile):
    try:
        name = safe_lora_name(file.filename or "")
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    destination = LORA_DIR / name
    if destination.exists():
        return JSONResponse({"error": "同名のLoRAが既にあります"}, status_code=409)
    temporary = destination.with_suffix(destination.suffix + ".uploading")
    total = 0
    try:
        with temporary.open("xb") as handle:
            while chunk := await file.read(8 * 1024 * 1024):
                total += len(chunk)
                if total > MAX_LORA_BYTES:
                    raise ValueError("LoRAファイルが大きすぎます")
                handle.write(chunk)
        temporary.replace(destination)
    except Exception as exc:
        temporary.unlink(missing_ok=True)
        return JSONResponse({"error": str(exc)}, status_code=400)
    touch_activity()
    return {"ok": True, "name": name, "size": total}


def _pod_request(action: str) -> None:
    pod_id = os.environ.get("RUNPOD_POD_ID", "")
    api_key = _pod_api_key()
    if not pod_id or not api_key:
        raise RuntimeError("RunPodのPod内でのみ実行できます")
    if action == "stop":
        url = f"https://rest.runpod.io/v1/pods/{pod_id}/stop"
        method = "POST"
    elif action == "terminate":
        url = f"https://rest.runpod.io/v1/pods/{pod_id}"
        method = "DELETE"
    else:
        raise ValueError("invalid action")
    request = urllib.request.Request(
        url,
        method=method,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        data=b"{}" if method == "POST" else None,
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310
            status = int(getattr(response, "status", 200))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"RunPod API HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("RunPod APIへ接続できません") from exc
    if not 200 <= status < 300:
        raise RuntimeError(f"RunPod API HTTP {status}")


@app.get("/api/pod/status")
def api_pod_status():
    state = _read_pod_action_state()
    if not state:
        return {
            "status": "idle",
            "message": "終了操作はまだ行われていません",
            "console_url": "https://www.runpod.io/console/pods",
        }
    return {**state, "console_url": "https://www.runpod.io/console/pods"}


@app.post("/api/pod/{action}")
def api_pod_action(action: str):
    if action not in {"stop", "terminate"}:
        return JSONResponse({"error": "操作が不正です"}, status_code=400)
    if not os.environ.get("RUNPOD_POD_ID") or not _pod_api_key():
        return JSONResponse(
            {"error": "自動終了用のRunPod APIキーがありません。RunPodコンソールから終了してください"},
            status_code=409,
        )
    _write_pod_action_state(
        status="pending",
        action=action,
        message="RunPodへ終了要求を送信します",
        requested_at=time.time(),
        finished_at=None,
    )

    def delayed_action() -> None:
        time.sleep(1.5)
        try:
            _pod_request(action)
            _write_pod_action_state(
                status="sent",
                message="RunPod APIが終了要求を受理しました。コンソールで最終状態を確認してください",
                finished_at=time.time(),
            )
        except Exception as exc:
            _write_pod_action_state(
                status="error",
                message=f"自動終了に失敗しました（{str(exc)[:160]}）。RunPodコンソールから終了してください",
                finished_at=time.time(),
            )

    threading.Thread(target=delayed_action, daemon=True).start()
    return JSONResponse(
        {
            "ok": True,
            "status": "pending",
            "action": action,
            "message": "終了要求を受け付けました。まだ完了ではありません",
            "console_url": "https://www.runpod.io/console/pods",
        },
        status_code=202,
    )


if not DISABLE_WORKER:
    threading.Thread(target=worker_loop, daemon=True).start()
