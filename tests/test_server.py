from __future__ import annotations

import hashlib
import json
import time

from fastapi.testclient import TestClient
from starlette.requests import Request

from app import config
from app import server
from app.server import app, same_origin


def install_dummy_models() -> None:
    for key in config.MODEL_DEFINITIONS:
        config.model_path(key).touch()
    (config.MODEL_ROOT / "text_encoders" / config.TEXT_ENCODER).touch()
    (config.MODEL_ROOT / "vae" / config.VAE).touch()
    for key in config.H3_FILE_KEYS:
        path = config.MODEL_ROOT / config.MODEL_FILES[key]["relative_path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()


def h3_acceptance_form() -> dict[str, str]:
    return {
        "territory_confirm": "yes",
        "license_confirm": "yes",
        "aup_confirm": "yes",
        "rights_confirm": "yes",
        "disclosure_confirm": "yes",
        "no_training_confirm": "yes",
        "reporting_confirm": "yes",
    }


def origin_request(origin: str, host: str = "internal:8080") -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "scheme": "http",
            "path": "/api/login",
            "raw_path": b"/api/login",
            "query_string": b"",
            "headers": [
                (b"origin", origin.encode("ascii")),
                (b"host", host.encode("ascii")),
            ],
            "client": ("127.0.0.1", 12345),
            "server": ("internal", 8080),
        }
    )


def test_same_origin_allows_exact_runpod_proxy(monkeypatch) -> None:
    monkeypatch.setenv("RUNPOD_POD_ID", "pod123abc")
    assert same_origin(origin_request("https://pod123abc-8080.proxy.runpod.net")) is True
    assert same_origin(origin_request("https://otherpod-8080.proxy.runpod.net")) is False


def test_same_origin_still_allows_direct_host(monkeypatch) -> None:
    monkeypatch.delenv("RUNPOD_POD_ID", raising=False)
    assert same_origin(origin_request("http://localhost:8080", "localhost:8080")) is True


def test_setup_login_config_generate_and_lora_upload() -> None:
    install_dummy_models()
    client = TestClient(app)

    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/setup"

    response = client.post(
        "/api/setup",
        data={"password": "test-password-123", "confirm": "test-password-123"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    response = client.post(
        "/api/login", data={"password": "test-password-123"}, follow_redirects=False
    )
    assert response.status_code == 303
    assert "acs_lite_session" in client.cookies

    response = client.get("/api/config")
    assert response.status_code == 200
    assert all(model["available"] for model in response.json()["models"])

    response = client.get("/api/models")
    assert response.status_code == 200
    assert {item["key"] for item in response.json()["packages"]} == {
        "turbo", "raw", "all", "h3", "recommended", "everything"
    }
    assert response.json()["download_disabled"] is True

    response = client.post("/api/models/install/h3")
    assert response.status_code == 451

    response = client.post("/api/models/install/turbo")
    assert response.status_code == 409

    response = client.post(
        "/api/loras",
        files={"file": ("demo.safetensors", b"safe-demo-content", "application/octet-stream")},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "demo.safetensors"

    response = client.post(
        "/api/generate",
        data={
            "model_key": "krea2_turbo",
            "prompt": "an adult person drinking iced coffee in a cafe",
            "negative": "",
            "ratio": "16:9",
            "style_key": "snapshot",
            "seed": "123",
            "lora_name": "demo.safetensors",
            "lora_strength": "0.8",
            "trigger_word": "subject_token",
        },
    )
    assert response.status_code == 200
    assert response.json()["seed"] == 123

    response = client.get("/api/h3/status")
    assert response.status_code == 200
    assert response.json()["region"]["allowed"] is True
    assert response.json()["accepted"] is False

    response = client.post(
        "/api/h3/accept",
        data=h3_acceptance_form(),
    )
    assert response.status_code == 200
    assert response.json()["accepted"] is True
    assert response.json()["terms_version"] == config.H3_TERMS_VERSION
    assert response.json()["license_integrity_ok"] is True
    record = json.loads(config.H3_ACCEPTANCE_FILE.read_text(encoding="utf-8"))
    assert record["license_sha256"] == config.H3_LICENSE_SHA256
    assert all(record["confirmations"].values())
    assert config.H3_ACCEPTANCE_LOG_FILE.read_text(encoding="utf-8").count("\n") == 1
    assert config.H3_ACCEPTANCE_FILE.stat().st_mode & 0o777 == 0o600

    response = client.post(
        "/api/video/generate",
        data={"mode": "t2v", "prompt": "a quiet cafe", "ratio": "16:9", "duration": "5", "seed": "321"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["seed"] == 321

    response = client.post(
        "/api/video/generate",
        data={
            "mode": "t2v",
            "prompt": "a deepfake of a real person without consent for fraud",
            "ratio": "16:9",
            "duration": "5",
        },
    )
    assert response.status_code == 422
    assert "nonconsensual_impersonation" in response.json()["categories"]
    safety_event = json.loads(config.H3_SAFETY_LOG_FILE.read_text(encoding="utf-8").splitlines()[-1])
    assert safety_event["stage"] == "request"
    assert "prompt" not in safety_event

    png_header = b"\x89PNG\r\n\x1a\n" + b"demo"
    response = client.post(
        "/api/video/generate",
        data={"mode": "flf", "prompt": "camera moves forward", "ratio": "9:16", "duration": "5"},
        files={
            "first_frame": ("first.png", png_header, "image/png"),
            "last_frame": ("last.png", png_header, "image/png"),
        },
    )
    assert response.status_code == 200, response.text

    output = config.OUTPUT_DIR / "job-999-minimax-h3-ai.mp4"
    output.write_bytes(b"demo-video")
    response = client.get(f"/api/outputs/{output.name}")
    assert response.status_code == 200
    assert response.headers["x-ai-generated-by"] == "MiniMax H3"


def test_h3_legal_documents_are_public_and_pinned() -> None:
    client = TestClient(app)
    client.cookies.clear()
    response = client.get("/legal/minimax-h3-license")
    assert response.status_code == 200
    assert hashlib.sha256(response.content).hexdigest() == config.H3_LICENSE_SHA256
    assert "Exhibit A" in response.text
    assert client.get("/legal/h3-terms").status_code == 200
    assert client.get("/legal/h3-enforcement").status_code == 200


def test_unauthenticated_api_is_rejected_after_setup() -> None:
    client = TestClient(app)
    client.cookies.clear()
    response = client.get("/api/config")
    assert response.status_code == 401


def test_cross_origin_write_is_rejected() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/login",
        data={"password": "test-password-123"},
        headers={"Origin": "https://example.invalid"},
    )
    assert response.status_code == 403


def test_pod_request_uses_explicit_secret_and_checks_http_status(monkeypatch) -> None:
    captured: dict[str, str] = {}

    class Response:
        status = 204

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def fake_urlopen(request, timeout):
        captured["authorization"] = request.headers["Authorization"]
        captured["method"] = request.method
        captured["timeout"] = str(timeout)
        return Response()

    monkeypatch.setenv("RUNPOD_POD_ID", "pod-test")
    monkeypatch.setenv("RUNPOD_API_KEY", "automatic-key")
    monkeypatch.setenv("ACS_RUNPOD_API_KEY", "explicit-secret")
    monkeypatch.setattr(server.urllib.request, "urlopen", fake_urlopen)
    server._pod_request("terminate")
    assert captured == {
        "authorization": "Bearer explicit-secret",
        "method": "DELETE",
        "timeout": "30",
    }


def test_pod_action_failure_is_not_reported_as_success(monkeypatch) -> None:
    config.POD_ACTION_STATE_FILE.unlink(missing_ok=True)
    monkeypatch.setenv("RUNPOD_POD_ID", "pod-test")
    monkeypatch.setenv("ACS_RUNPOD_API_KEY", "explicit-secret")

    def fail_request(_action: str) -> None:
        raise RuntimeError("RunPod API HTTP 401")

    monkeypatch.setattr(server, "_pod_request", fail_request)
    response = server.api_pod_action("terminate")
    assert response.status_code == 202
    assert json.loads(response.body)["status"] == "pending"

    deadline = time.time() + 3
    state = server.api_pod_status()
    while state.get("status") == "pending" and time.time() < deadline:
        time.sleep(0.05)
        state = server.api_pod_status()
    assert state["status"] == "error"
    assert "HTTP 401" in state["message"]
    assert state["console_url"] == "https://www.runpod.io/console/pods"
