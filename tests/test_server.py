from __future__ import annotations

from fastapi.testclient import TestClient

from app import config
from app.server import app


def install_dummy_models() -> None:
    for key in config.MODEL_DEFINITIONS:
        config.model_path(key).touch()
    (config.MODEL_ROOT / "text_encoders" / config.TEXT_ENCODER).touch()
    (config.MODEL_ROOT / "vae" / config.VAE).touch()


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
    assert {item["key"] for item in response.json()["packages"]} == {"turbo", "raw", "all"}
    assert response.json()["download_disabled"] is True

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
