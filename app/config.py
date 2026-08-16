from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse


APP_NAME = "ACS ImageGen Lite"
VERSION = "0.4.0"

APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent
DATA_DIR = Path(os.environ.get("ACS_LITE_DATA_DIR", "/workspace/acs-imagegen-lite-data"))
MODEL_ROOT = Path(os.environ.get("ACS_MODEL_ROOT", "/workspace/models"))
COMFY_URL = os.environ.get("ACS_COMFY_URL", "http://127.0.0.1:8188").rstrip("/")
_COMFY_PARSED = urlparse(COMFY_URL)
if _COMFY_PARSED.scheme != "http" or _COMFY_PARSED.hostname not in {"127.0.0.1", "localhost", "::1"}:
    raise RuntimeError("ACS_COMFY_URL must use local HTTP only")

DB_PATH = DATA_DIR / "jobs.db"
OUTPUT_DIR = DATA_DIR / "outputs"
COMFY_INPUT_DIR = Path(os.environ.get("ACS_COMFY_INPUT_DIR", "/workspace/comfy-input"))
PASSWORD_FILE = DATA_DIR / ".password"
SESSION_KEY_FILE = DATA_DIR / ".session_key"
ACTIVITY_FILE = DATA_DIR / "last_activity"
H3_ACCEPTANCE_FILE = DATA_DIR / "minimax_h3_acceptance.json"
H3_ACCEPTANCE_LOG_FILE = DATA_DIR / "minimax_h3_acceptance_log.jsonl"
H3_SAFETY_LOG_FILE = DATA_DIR / "minimax_h3_safety_log.jsonl"
KREA_ACCEPTANCE_FILE = DATA_DIR / "krea2_acceptance.json"
KREA_ACCEPTANCE_LOG_FILE = DATA_DIR / "krea2_acceptance_log.jsonl"
KREA_SAFETY_LOG_FILE = DATA_DIR / "krea2_safety_log.jsonl"
ZIMAGE_SAFETY_LOG_FILE = DATA_DIR / "z_image_safety_log.jsonl"
LORA_DIR = MODEL_ROOT / "loras"
MODEL_STATE_FILE = DATA_DIR / "model_download_state.json"
MODEL_VERIFIED_FILE = DATA_DIR / "verified_models.json"
POD_ACTION_STATE_FILE = DATA_DIR / "pod_action_state.json"

KREA_LICENSE_VERSION = "2026-06-22-v1"
KREA_LICENSE_SHA256 = "b82a2805162bde714a4eb27b9063c4fc3345d08a30be055134a6160e5430ba74"
KREA_LICENSE_URL = "https://huggingface.co/Comfy-Org/Krea-2/blob/main/LICENSE.pdf"
KREA_AUP_URL = "https://www.krea.ai/krea-2-use-policy"
KREA_TERMS_VERSION = "2026-08-14-1"
KREA_TERMS_PATH = PROJECT_DIR / "docs" / "KREA2-TERMS.md"

# Z-Image Turboの上流はApache License 2.0で、追加のAcceptable Use Policyや
# 同意ゲートを課していない（2026-08-16にモデルカードとリポジトリのメタデータを確認）。
# そのため同意ゲートは設けず、出典・ライセンス表示とACS側の安全検査だけを適用する。
ZIMAGE_MODEL_NAME = "Z-Image Turbo"
ZIMAGE_LICENSE_NAME = "Apache License 2.0"
ZIMAGE_LICENSE_URL = "https://huggingface.co/Tongyi-MAI/Z-Image-Turbo"
ZIMAGE_LICENSE_PATH = PROJECT_DIR / "APACHE-2.0-LICENSE.txt"
ZIMAGE_TERMS_PATH = PROJECT_DIR / "docs" / "Z-IMAGE-TERMS.md"
ZIMAGE_TERMS_VERSION = "2026-08-16-1"
ZIMAGE_UPSTREAM_REPO = "https://huggingface.co/Tongyi-MAI/Z-Image-Turbo"
ZIMAGE_REPACK_REPO = "https://huggingface.co/Comfy-Org/z_image_turbo"

MODEL_REPOSITORY = "https://huggingface.co/Comfy-Org/Krea-2/resolve/main"
MODEL_FILES = {
    "text_encoder": {
        "repo_id": "Comfy-Org/Krea-2",
        "revision": "952f49d49653cb42e7d6cf7cbfad74738073ec7d",
        "relative_path": "text_encoders/qwen3vl_4b_fp8_scaled.safetensors",
        "size": 5_242_467_968,
        "sha256": "54bd5144df0bbc25dd6ccadfcb826b521445a1b06ae5a42570bdd2974ca87094",
    },
    "vae": {
        "repo_id": "Comfy-Org/Krea-2",
        "revision": "952f49d49653cb42e7d6cf7cbfad74738073ec7d",
        "relative_path": "vae/qwen_image_vae.safetensors",
        "size": 253_806_246,
        "sha256": "a70580f0213e67967ee9c95f05bb400e8fb08307e017a924bf3441223e023d1f",
    },
    "turbo": {
        "repo_id": "Comfy-Org/Krea-2",
        "revision": "952f49d49653cb42e7d6cf7cbfad74738073ec7d",
        "relative_path": "diffusion_models/krea2_turbo_fp8_scaled.safetensors",
        "size": 13_141_730_784,
        "sha256": "eb4dd8c612cfd10f64f25b057e6e6bbcb5737c94a7372177e456dbf7579502f1",
    },
    "raw": {
        "repo_id": "Comfy-Org/Krea-2",
        "revision": "952f49d49653cb42e7d6cf7cbfad74738073ec7d",
        "relative_path": "diffusion_models/krea2_raw_fp8_scaled.safetensors",
        "size": 13_141_730_784,
        "sha256": "48cd5d6c100297968349b41a8e77c6591d1dac18a215807f5f25f59e5c54cd61",
    },
    "h3_diffusion": {
        "repo_id": "Comfy-Org/MiniMax-H3",
        "revision": "014cd40f7e177756c6b2473c0d93b1c89a790dd2",
        "repository": "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main",
        "relative_path": "diffusion_models/minimax_h3_fl2va_pruned_fp8_scaled.safetensors",
        "size": 20_958_205_608,
        "sha256": "12944c1f7791637e7de12208aef04da82bd26b95271b1b47d817364315ade993",
    },
    "h3_text_encoder": {
        "repo_id": "Comfy-Org/MiniMax-H3",
        "revision": "014cd40f7e177756c6b2473c0d93b1c89a790dd2",
        "repository": "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main",
        "relative_path": "text_encoders/qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
        "size": 27_141_342_152,
        "sha256": "bc2ced0fbea64757fa9acddccfc0b3f4819d1dcf1da6c124d690d368be283923",
    },
    "h3_video_vae": {
        "repo_id": "Comfy-Org/MiniMax-H3",
        "revision": "014cd40f7e177756c6b2473c0d93b1c89a790dd2",
        "repository": "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main",
        "relative_path": "vae/minimax_h3_video_vae_fp16.safetensors",
        "size": 5_207_808_496,
        "sha256": "7c1f131492e7eddacaac9069a61b81bdd39de5cc96561e677c5eab1cdce5e522",
    },
    "h3_audio_vae": {
        "repo_id": "Comfy-Org/MiniMax-H3",
        "revision": "014cd40f7e177756c6b2473c0d93b1c89a790dd2",
        "repository": "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main",
        "relative_path": "vae/minimax_h3_audio_vae_fp32.safetensors",
        "size": 605_254_808,
        "sha256": "8e505d95dd1561d47abd43d4238fd40d9bb1ae9e147ed0a4cba778d76ae4db48",
    },
    # Comfy-Org公式リパックの配置は`split_files/`配下なので、取得元パスと
    # ComfyUIの配置パスを`remote_path` / `relative_path`で分ける。
    "zimage_diffusion": {
        "repo_id": "Comfy-Org/z_image_turbo",
        "revision": "d24c4cf2a0cd98a42f23467e27e3d76ee9438b8e",
        "repository": "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/d24c4cf2a0cd98a42f23467e27e3d76ee9438b8e",
        "remote_path": "split_files/diffusion_models/z_image_turbo_int8_convrot.safetensors",
        "relative_path": "diffusion_models/z_image_turbo_int8_convrot.safetensors",
        "size": 6_201_001_296,
        "sha256": "be517ebd47c912a5626a588e1aeea43e6be4a43c0cdcd2b48a2a780d9f358635",
    },
    "zimage_text_encoder": {
        "repo_id": "Comfy-Org/z_image_turbo",
        "revision": "d24c4cf2a0cd98a42f23467e27e3d76ee9438b8e",
        "repository": "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/d24c4cf2a0cd98a42f23467e27e3d76ee9438b8e",
        "remote_path": "split_files/text_encoders/qwen_3_4b_fp8_mixed.safetensors",
        "relative_path": "text_encoders/qwen_3_4b_fp8_mixed.safetensors",
        "size": 5_631_994_051,
        "sha256": "72450b19758172c5a7273cf7de729d1c17e7f434a104a00167624cba94f68f15",
    },
    "zimage_vae": {
        "repo_id": "Comfy-Org/z_image_turbo",
        "revision": "d24c4cf2a0cd98a42f23467e27e3d76ee9438b8e",
        "repository": "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/d24c4cf2a0cd98a42f23467e27e3d76ee9438b8e",
        "remote_path": "split_files/vae/ae.safetensors",
        "relative_path": "vae/ae.safetensors",
        "size": 335_304_388,
        "sha256": "afc8e28272cd15db3919bacdb6918ce9c1ed22e96cb12c4d5ed0fba823529e38",
    },
}

H3_FILE_KEYS = ("h3_diffusion", "h3_text_encoder", "h3_video_vae", "h3_audio_vae")
ZIMAGE_FILE_KEYS = ("zimage_diffusion", "zimage_text_encoder", "zimage_vae")

MODEL_PACKAGES = {
    "turbo": {
        "label": "Krea2 Turbo",
        "description": "初めての方におすすめ。高速な画像生成",
        "file_keys": ("text_encoder", "vae", "turbo"),
        "requires_krea_terms": True,
    },
    "raw": {
        "label": "Krea2 Raw",
        "description": "品質優先。Turbo導入後は約13.1GB追加",
        "file_keys": ("text_encoder", "vae", "raw"),
        "requires_krea_terms": True,
    },
    "all": {
        "label": "Turbo + Raw",
        "description": "2モデルをまとめて準備",
        "file_keys": ("text_encoder", "vae", "turbo", "raw"),
        "requires_krea_terms": True,
    },
    "zimage": {
        "label": "Z-Image Turbo",
        "description": "いちばん軽い画像生成。16GB級GPUで動く約12.2GB",
        "file_keys": ZIMAGE_FILE_KEYS,
    },
    "h3": {
        "label": "MiniMax H3 動画",
        "description": "Text / Image / First-Last Frame動画。約53.9GB",
        "file_keys": H3_FILE_KEYS,
        "requires_h3_terms": True,
    },
    "recommended": {
        "label": "おすすめ：Krea2 Turbo + MiniMax H3",
        "description": "画像と3種類の動画をまとめて準備。約72.6GB",
        "file_keys": ("text_encoder", "vae", "turbo", *H3_FILE_KEYS),
        "requires_krea_terms": True,
        "requires_h3_terms": True,
    },
    "everything": {
        "label": "すべて：Krea2 Turbo + Raw + Z-Image + MiniMax H3",
        "description": "画像3モデルと動画をすべて準備。約97.9GB",
        "file_keys": ("text_encoder", "vae", "turbo", "raw", *ZIMAGE_FILE_KEYS, *H3_FILE_KEYS),
        "requires_krea_terms": True,
        "requires_h3_terms": True,
    },
}

MODEL_DEFINITIONS = {
    "krea2_turbo": {
        "label": "Krea2 Turbo（高速・8 steps）",
        "engine": "krea2",
        "unet": "krea2_turbo_fp8_scaled.safetensors",
        "steps": 8,
        "cfg": 1.0,
        "negative": False,
    },
    "krea2_raw": {
        "label": "Krea2 Raw（高品質・24 steps）",
        "engine": "krea2",
        "unet": "krea2_raw_fp8_scaled.safetensors",
        "steps": 24,
        "cfg": 4.0,
        "negative": True,
    },
    # Z-Image Turboの8 steps / cfg 1.0 / res_multistep / simple / shift 3.0は
    # 公式蒸留グリッドそのものなので変更しない（ComfyUI公式int8テンプレートと同値）。
    "zimage_turbo": {
        "label": "Z-Image Turbo（軽量・8 steps）",
        "engine": "zimage",
        "unet": "z_image_turbo_int8_convrot.safetensors",
        "steps": 8,
        "cfg": 1.0,
        "negative": False,
    },
}

TEXT_ENCODER = "qwen3vl_4b_fp8_scaled.safetensors"
VAE = "qwen_image_vae.safetensors"
ZIMAGE_TEXT_ENCODER = "qwen_3_4b_fp8_mixed.safetensors"
ZIMAGE_VAE = "ae.safetensors"
ZIMAGE_SHIFT = 3.0
ZIMAGE_SAMPLER = "res_multistep"
ZIMAGE_SCHEDULER = "simple"

# エンジンごとの共有ファイル（text encoder, VAE）
ENGINE_ASSETS = {
    "krea2": (TEXT_ENCODER, VAE),
    "zimage": (ZIMAGE_TEXT_ENCODER, ZIMAGE_VAE),
}

H3_MODEL_KEY = "minimax_h3"
H3_LICENSE_VERSION = "2026-08-02"
H3_LICENSE_URL = "https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE"
H3_LICENSE_SHA256 = "59b99642b95ea21630e311198ddbfffbfe05aadba0c2f5d884cbdf4efcc90f44"
H3_TERMS_VERSION = "2026-08-14-1"
H3_LICENSE_PATH = PROJECT_DIR / "MINIMAX_H3_LICENSE.txt"
H3_TERMS_PATH = PROJECT_DIR / "docs" / "H3-TERMS.md"
H3_ENFORCEMENT_PATH = PROJECT_DIR / "docs" / "H3-ENFORCEMENT.md"
H3_REPORT_URL = os.environ.get(
    "ACS_H3_REPORT_URL",
    "mailto:info@acs-developer.com?subject=MiniMax%20H3%20suspected%20violation",
)
# 公開配布版は日本のRunPodリージョンだけを許可し、環境変数による解除口を設けない。
H3_ALLOWED_DC_PREFIXES = ("AP-JP-1",)
H3_SIZES = {
    "16:9": (864, 480),
    "9:16": (480, 864),
    "1:1": (672, 672),
}

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
MAX_INPUT_IMAGE_BYTES = int(os.environ.get("ACS_MAX_INPUT_IMAGE_BYTES", str(25 * 1024**2)))
JOB_TIMEOUT_SEC = int(os.environ.get("ACS_JOB_TIMEOUT_SEC", "3600"))
COOKIE_SECURE = os.environ.get("ACS_COOKIE_SECURE", "1") != "0"
DISABLE_WORKER = os.environ.get("ACS_LITE_DISABLE_WORKER", "0") == "1"
DISABLE_MODEL_DOWNLOAD = os.environ.get("ACS_LITE_DISABLE_MODEL_DOWNLOAD", "0") == "1"


def ensure_directories() -> None:
    for path in (DATA_DIR, OUTPUT_DIR, COMFY_INPUT_DIR, MODEL_ROOT / "diffusion_models", MODEL_ROOT / "text_encoders", MODEL_ROOT / "vae", LORA_DIR):
        path.mkdir(parents=True, exist_ok=True)


def model_path(model_key: str) -> Path:
    return MODEL_ROOT / "diffusion_models" / MODEL_DEFINITIONS[model_key]["unet"]


def model_engine(model_key: str) -> str:
    return str(MODEL_DEFINITIONS.get(model_key, {}).get("engine", "krea2"))


def model_available(model_key: str) -> bool:
    definition = MODEL_DEFINITIONS.get(model_key)
    if not definition:
        return False
    text_encoder, vae = ENGINE_ASSETS[model_engine(model_key)]
    required = (
        model_path(model_key),
        MODEL_ROOT / "text_encoders" / text_encoder,
        MODEL_ROOT / "vae" / vae,
    )
    return all(path.is_file() for path in required)


def zimage_available() -> bool:
    return model_available("zimage_turbo")


def h3_available() -> bool:
    return all((MODEL_ROOT / str(MODEL_FILES[key]["relative_path"])).is_file() for key in H3_FILE_KEYS)


def h3_region_status() -> dict[str, object]:
    dc_id = os.environ.get("RUNPOD_DC_ID", "").strip()
    allowed = bool(dc_id and any(dc_id.startswith(prefix) for prefix in H3_ALLOWED_DC_PREFIXES))
    if allowed:
        reason = f"RunPodリージョン {dc_id} はこの配布設定の許可対象です"
    elif dc_id:
        reason = f"RunPodリージョン {dc_id} ではH3を有効化できません"
    else:
        reason = "RunPodリージョンを確認できないためH3を有効化できません"
    return {"allowed": allowed, "dc_id": dc_id or None, "reason": reason}
