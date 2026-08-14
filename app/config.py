from __future__ import annotations

import os
from pathlib import Path


APP_NAME = "ACS ImageGen Lite"
VERSION = "0.2.0-rc1"

APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent
DATA_DIR = Path(os.environ.get("ACS_LITE_DATA_DIR", "/workspace/acs-imagegen-lite-data"))
MODEL_ROOT = Path(os.environ.get("ACS_MODEL_ROOT", "/workspace/models"))
COMFY_URL = os.environ.get("ACS_COMFY_URL", "http://127.0.0.1:8188").rstrip("/")

DB_PATH = DATA_DIR / "jobs.db"
OUTPUT_DIR = DATA_DIR / "outputs"
PASSWORD_FILE = DATA_DIR / ".password"
SESSION_KEY_FILE = DATA_DIR / ".session_key"
ACTIVITY_FILE = DATA_DIR / "last_activity"
LORA_DIR = MODEL_ROOT / "loras"
MODEL_STATE_FILE = DATA_DIR / "model_download_state.json"
MODEL_VERIFIED_FILE = DATA_DIR / "verified_models.json"

MODEL_REPOSITORY = "https://huggingface.co/Comfy-Org/Krea-2/resolve/main"
MODEL_FILES = {
    "text_encoder": {
        "relative_path": "text_encoders/qwen3vl_4b_fp8_scaled.safetensors",
        "size": 5_242_467_968,
        "sha256": "54bd5144df0bbc25dd6ccadfcb826b521445a1b06ae5a42570bdd2974ca87094",
    },
    "vae": {
        "relative_path": "vae/qwen_image_vae.safetensors",
        "size": 253_806_246,
        "sha256": "a70580f0213e67967ee9c95f05bb400e8fb08307e017a924bf3441223e023d1f",
    },
    "turbo": {
        "relative_path": "diffusion_models/krea2_turbo_fp8_scaled.safetensors",
        "size": 13_141_730_784,
        "sha256": "eb4dd8c612cfd10f64f25b057e6e6bbcb5737c94a7372177e456dbf7579502f1",
    },
    "raw": {
        "relative_path": "diffusion_models/krea2_raw_fp8_scaled.safetensors",
        "size": 13_141_730_784,
        "sha256": "48cd5d6c100297968349b41a8e77c6591d1dac18a215807f5f25f59e5c54cd61",
    },
}

MODEL_PACKAGES = {
    "turbo": {
        "label": "Krea2 Turbo",
        "description": "初めての方におすすめ。高速な画像生成",
        "file_keys": ("text_encoder", "vae", "turbo"),
    },
    "raw": {
        "label": "Krea2 Raw",
        "description": "品質優先。Turbo導入後は約13.1GB追加",
        "file_keys": ("text_encoder", "vae", "raw"),
    },
    "all": {
        "label": "Turbo + Raw",
        "description": "2モデルをまとめて準備",
        "file_keys": ("text_encoder", "vae", "turbo", "raw"),
    },
}

MODEL_DEFINITIONS = {
    "krea2_turbo": {
        "label": "Krea2 Turbo（高速・8 steps）",
        "unet": "krea2_turbo_fp8_scaled.safetensors",
        "steps": 8,
        "cfg": 1.0,
        "negative": False,
    },
    "krea2_raw": {
        "label": "Krea2 Raw（高品質・24 steps）",
        "unet": "krea2_raw_fp8_scaled.safetensors",
        "steps": 24,
        "cfg": 4.0,
        "negative": True,
    },
}

TEXT_ENCODER = "qwen3vl_4b_fp8_scaled.safetensors"
VAE = "qwen_image_vae.safetensors"

SIZES = {
    "16:9": (1344, 768),
    "9:16": (768, 1344),
    "1:1": (1024, 1024),
    "4:3": (1152, 864),
    "3:4": (864, 1152),
}

STYLES = {
    "none": ("スタイルなし", ""),
    "snapshot": (
        "自然なスナップ写真",
        "natural candid photography, realistic lighting, coherent hands and objects",
    ),
    "studio": (
        "スタジオ写真",
        "professional studio photography, controlled soft light, clean composition",
    ),
    "cinematic": (
        "シネマティック",
        "cinematic composition, motivated lighting, subtle film color grading",
    ),
}

MAX_PROMPT_LENGTH = int(os.environ.get("ACS_MAX_PROMPT_LENGTH", "4000"))
MAX_LORA_BYTES = int(os.environ.get("ACS_MAX_LORA_BYTES", str(2 * 1024**3)))
JOB_TIMEOUT_SEC = int(os.environ.get("ACS_JOB_TIMEOUT_SEC", "3600"))
COOKIE_SECURE = os.environ.get("ACS_COOKIE_SECURE", "1") != "0"
DISABLE_WORKER = os.environ.get("ACS_LITE_DISABLE_WORKER", "0") == "1"
DISABLE_MODEL_DOWNLOAD = os.environ.get("ACS_LITE_DISABLE_MODEL_DOWNLOAD", "0") == "1"


def ensure_directories() -> None:
    for path in (DATA_DIR, OUTPUT_DIR, MODEL_ROOT / "diffusion_models", MODEL_ROOT / "text_encoders", MODEL_ROOT / "vae", LORA_DIR):
        path.mkdir(parents=True, exist_ok=True)


def model_path(model_key: str) -> Path:
    return MODEL_ROOT / "diffusion_models" / MODEL_DEFINITIONS[model_key]["unet"]


def model_available(model_key: str) -> bool:
    definition = MODEL_DEFINITIONS.get(model_key)
    if not definition:
        return False
    required = (
        model_path(model_key),
        MODEL_ROOT / "text_encoders" / TEXT_ENCODER,
        MODEL_ROOT / "vae" / VAE,
    )
    return all(path.is_file() for path in required)
