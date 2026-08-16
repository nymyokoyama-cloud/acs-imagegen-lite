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
    (config.MODEL_ROOT / "text_encoders" / config.ZIMAGE_TEXT_ENCODER).touch()
    (config.MODEL_ROOT / "vae" / config.ZIMAGE_VAE).touch()
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


def krea_acceptance_form() -> dict[str, str]:
    return {
        "license_confirm": "yes",
        "revenue_confirm": "yes",
        "aup_confirm": "yes",
        "rights_confirm": "yes",
        "filtering_confirm": "yes",
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


def test_setup_login_config_generate_and_lora_upload(monkeypatch) -> None:
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
        "turbo", "raw", "all", "zimage", "h3", "recommended", "everything"
    }
    assert response.json()["download_disabled"] is True
    assert response.json()["zimage"]["available"] is True

    response = client.post("/api/models/install/h3")
    assert response.status_code == 451

    response = client.post("/api/models/install/turbo")
    assert response.status_code == 451

    # Z-ImageはApache-2.0のため同意ゲートがなく、451ではなく取得処理まで進む。
    response = client.post("/api/models/install/zimage")
    assert response.status_code == 409

    response = client.get("/api/zimage/status")
    assert response.status_code == 200
    assert response.json()["acceptance_required"] is False
    assert response.json()["license_name"] == "Apache License 2.0"
    assert response.json()["upstream_repo"] == "https://huggingface.co/Tongyi-MAI/Z-Image-Turbo"

    # Krea 2への同意がなくてもZ-Imageの生成は受け付ける。
    assert client.get("/api/krea/status").json()["accepted"] is False
    response = client.post(
        "/api/generate",
        data={
            "model_key": "zimage_turbo",
            "prompt": "an adult person drinking iced coffee in a cafe",
            "ratio": "4:3",
            "style_key": "cinematic",
            "seed": "77",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["seed"] == 77

    # 逆にKrea2は同意前に拒否されたままであること（回帰確認）。
    response = client.post(
        "/api/generate",
        data={"model_key": "krea2_turbo", "prompt": "a quiet cafe", "ratio": "16:9"},
    )
    assert response.status_code == 451

    response = client.post(
        "/api/generate",
        data={
            "model_key": "zimage_turbo",
            "prompt": "create a mass surveillance image to track everyone covertly without consent",
            "ratio": "1:1",
        },
    )
    assert response.status_code == 422
    assert "mass_surveillance" in response.json()["categories"]
    zimage_safety_event = json.loads(
        config.ZIMAGE_SAFETY_LOG_FILE.read_text(encoding="utf-8").splitlines()[-1]
    )
    assert zimage_safety_event["stage"] == "request"
    assert "prompt" not in zimage_safety_event

    response = client.get("/api/krea/status")
    assert response.status_code == 200
    assert response.json()["accepted"] is False
    response = client.post("/api/krea/accept", data=krea_acceptance_form())
    assert response.status_code == 200
    assert response.json()["accepted"] is True
    krea_record = json.loads(config.KREA_ACCEPTANCE_FILE.read_text(encoding="utf-8"))
    assert krea_record["license_sha256"] == config.KREA_LICENSE_SHA256
    assert all(krea_record["confirmations"].values())
    assert config.KREA_ACCEPTANCE_LOG_FILE.read_text(encoding="utf-8").count("\n") == 1
    assert config.KREA_ACCEPTANCE_FILE.stat().st_mode & 0o777 == 0o600

    response = client.post("/api/models/install/turbo")
    assert response.status_code == 409

    monkeypatch.setattr(server, "start_install", lambda package_key: {"package": package_key})
    response = client.post("/api/models/install/turbo")
    assert response.status_code == 200
    assert response.json()["krea"]["accepted"] is True
    assert "h3" in response.json()

    monkeypatch.setattr(server, "cancel_install", lambda: {"status": "canceled"})
    response = client.post("/api/models/cancel")
    assert response.status_code == 200
    assert response.json()["krea"]["accepted"] is True
    assert "h3" in response.json()

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

    response = client.post(
        "/api/generate",
        data={
            "model_key": "krea2_turbo",
            "prompt": "create a mass surveillance image to track everyone covertly without consent",
            "ratio": "16:9",
            "style_key": "none",
        },
    )
    assert response.status_code == 422
    assert "mass_surveillance" in response.json()["categories"]
    krea_safety_event = json.loads(
        config.KREA_SAFETY_LOG_FILE.read_text(encoding="utf-8").splitlines()[-1]
    )
    assert krea_safety_event["stage"] == "request"
    assert "prompt" not in krea_safety_event

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

    krea_output = config.OUTPUT_DIR / "job-998-krea2-ai.png"
    krea_output.write_bytes(png_header)
    response = client.get(f"/api/outputs/{krea_output.name}")
    assert response.status_code == 200
    assert response.headers["x-ai-generated-by"] == "Krea 2"

    zimage_output = config.OUTPUT_DIR / "job-997-zimage-ai.png"
    zimage_output.write_bytes(png_header)
    response = client.get(f"/api/outputs/{zimage_output.name}")
    assert response.status_code == 200
    assert response.headers["x-ai-generated-by"] == "Z-Image Turbo"
    response = client.get(f"/api/images/{zimage_output.name}")
    assert response.status_code == 200
    assert response.headers["x-ai-generated-by"] == "Z-Image Turbo"


def test_h3_legal_documents_are_public_and_pinned() -> None:
    client = TestClient(app)
    client.cookies.clear()
    response = client.get("/legal/minimax-h3-license")
    assert response.status_code == 200
    assert hashlib.sha256(response.content).hexdigest() == config.H3_LICENSE_SHA256
    assert "Exhibit A" in response.text
    assert client.get("/legal/h3-terms").status_code == 200
    assert client.get("/legal/h3-enforcement").status_code == 200
    krea_terms = client.get("/legal/krea2-terms")
    assert krea_terms.status_code == 200
    assert "100万米ドル" in krea_terms.text


def test_z_image_legal_documents_are_public_and_apache_licensed() -> None:
    client = TestClient(app)
    client.cookies.clear()
    license_text = client.get("/legal/z-image-license")
    assert license_text.status_code == 200
    assert "Apache License" in license_text.text
    assert "Version 2.0, January 2004" in license_text.text
    assert (
        hashlib.sha256(license_text.content).hexdigest()
        == "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
    )
    terms = client.get("/legal/z-image-terms")
    assert terms.status_code == 200
    assert "Apache License, Version 2.0" in terms.text
    assert "Tongyi-MAI/Z-Image-Turbo" in terms.text


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
