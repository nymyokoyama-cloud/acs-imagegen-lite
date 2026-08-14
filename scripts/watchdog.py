from __future__ import annotations

import json
import os
import sqlite3
import time
import urllib.request
from pathlib import Path


DATA_DIR = Path(os.environ.get("ACS_LITE_DATA_DIR", "/workspace/acs-imagegen-lite-data"))
DB_PATH = DATA_DIR / "jobs.db"
ACTIVITY_FILE = DATA_DIR / "last_activity"
MODEL_STATE_FILE = DATA_DIR / "model_download_state.json"
POD_ACTION_STATE_FILE = DATA_DIR / "pod_action_state.json"
IDLE_SECONDS = max(5, int(os.environ.get("ACS_IDLE_MINUTES", "20"))) * 60
MAX_UPTIME_SECONDS = max(15, int(os.environ.get("ACS_MAX_UPTIME_MINUTES", "180"))) * 60
CHECK_SECONDS = max(10, int(os.environ.get("ACS_WATCHDOG_INTERVAL", "30")))


def write_action_state(**values: object) -> None:
    try:
        state = json.loads(POD_ACTION_STATE_FILE.read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            state = {}
    except (OSError, ValueError, TypeError):
        state = {}
    state.update(values)
    temporary = POD_ACTION_STATE_FILE.with_name(f".{POD_ACTION_STATE_FILE.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(POD_ACTION_STATE_FILE)


def active_job_exists() -> bool:
    try:
        state = json.loads(MODEL_STATE_FILE.read_text(encoding="utf-8"))
        if state.get("status") in {"starting", "downloading", "verifying"}:
            return True
    except (OSError, ValueError, AttributeError):
        pass
    if not DB_PATH.exists():
        return False
    try:
        with sqlite3.connect(DB_PATH, timeout=3) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE status IN ('queued','running')"
            ).fetchone()
        return bool(row and row[0])
    except (sqlite3.Error, OSError):
        return True


def selected_action() -> str:
    configured = os.environ.get("ACS_IDLE_ACTION", "auto").lower()
    if configured in {"stop", "terminate"}:
        return configured
    return "terminate"


def request_pod_action(action: str) -> None:
    pod_id = os.environ.get("RUNPOD_POD_ID", "")
    api_key = os.environ.get("ACS_RUNPOD_API_KEY", "") or os.environ.get("RUNPOD_API_KEY", "")
    if not pod_id or not api_key:
        raise RuntimeError("RUNPOD_POD_ID or RUNPOD_API_KEY is missing")
    if action == "stop":
        url, method = f"https://rest.runpod.io/v1/pods/{pod_id}/stop", "POST"
    else:
        url, method = f"https://rest.runpod.io/v1/pods/{pod_id}", "DELETE"
    request = urllib.request.Request(
        url,
        method=method,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        data=b"{}" if method == "POST" else None,
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        status = int(getattr(response, "status", 200))
    if not 200 <= status < 300:
        raise RuntimeError(f"RunPod API HTTP {status}")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    started_at = time.time()
    if not ACTIVITY_FILE.exists():
        ACTIVITY_FILE.touch()
    while True:
        time.sleep(CHECK_SECONDS)
        now = time.time()
        if active_job_exists():
            ACTIVITY_FILE.touch()
            continue
        idle_for = now - ACTIVITY_FILE.stat().st_mtime
        reason = None
        if now - started_at >= MAX_UPTIME_SECONDS:
            reason = "maximum uptime"
        elif idle_for >= IDLE_SECONDS:
            reason = "idle timeout"
        if not reason:
            continue
        action = selected_action()
        print(json.dumps({"watchdog": reason, "action": action}), flush=True)
        write_action_state(
            status="pending",
            action=action,
            message=f"自動終了を実行中（{reason}）",
            requested_at=time.time(),
            finished_at=None,
        )
        try:
            request_pod_action(action)
            write_action_state(
                status="sent",
                message="RunPod APIが自動終了要求を受理しました。コンソールで最終状態を確認してください",
                finished_at=time.time(),
            )
            return
        except Exception as exc:
            print(json.dumps({"watchdog_error": str(exc)}), flush=True)
            write_action_state(
                status="error",
                message="自動終了に失敗しました。RunPodコンソールから終了してください",
                finished_at=time.time(),
            )
            time.sleep(min(300, CHECK_SECONDS * 4))


if __name__ == "__main__":
    main()
