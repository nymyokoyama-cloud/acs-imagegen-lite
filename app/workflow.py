from __future__ import annotations

from typing import Any

from .config import (
    MODEL_DEFINITIONS,
    STYLES,
    TEXT_ENCODER,
    VAE,
    ZIMAGE_SAMPLER,
    ZIMAGE_SCHEDULER,
    ZIMAGE_SHIFT,
    ZIMAGE_TEXT_ENCODER,
    ZIMAGE_VAE,
)


def compose_prompt(prompt: str, trigger_word: str = "", style_key: str = "none") -> str:
    parts: list[str] = []
    trigger_word = trigger_word.strip().strip(",")
    prompt = prompt.strip()
    if trigger_word:
        parts.append(trigger_word)
    if prompt:
        parts.append(prompt)
    suffix = STYLES.get(style_key, STYLES["none"])[1]
    if suffix:
        parts.append(suffix)
    return ", ".join(parts)


def build_workflow(
    model_key: str,
    prompt: str,
    negative: str,
    width: int,
    height: int,
    seed: int,
    lora_name: str | None = None,
    lora_strength: float = 1.0,
    trigger_word: str = "",
    style_key: str = "none",
) -> dict[str, dict[str, Any]]:
    if model_key not in MODEL_DEFINITIONS:
        raise ValueError(f"unknown model: {model_key}")
    definition = MODEL_DEFINITIONS[model_key]
    if definition.get("engine") == "zimage":
        return build_zimage_workflow(
            model_key=model_key,
            prompt=prompt,
            width=width,
            height=height,
            seed=seed,
            lora_name=lora_name,
            lora_strength=lora_strength,
            trigger_word=trigger_word,
            style_key=style_key,
        )
    positive_text = compose_prompt(prompt, trigger_word, style_key)
    if not positive_text:
        raise ValueError("prompt is empty")

    graph: dict[str, dict[str, Any]] = {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": definition["unet"], "weight_dtype": "default"},
        },
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": TEXT_ENCODER, "type": "krea2", "device": "default"},
        },
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": positive_text}},
        "6": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1},
        },
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["6", 0],
                "seed": seed,
                "steps": definition["steps"],
                "cfg": definition["cfg"],
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
            },
        },
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {
            "class_type": "SaveImage",
            "inputs": {"images": ["8", 0], "filename_prefix": "ACS_ImageGen_Lite"},
        },
    }

    if definition["negative"]:
        graph["5"] = {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["2", 0], "text": negative.strip()},
        }
    else:
        graph["5"] = {
            "class_type": "ConditioningZeroOut",
            "inputs": {"conditioning": ["4", 0]},
        }

    if lora_name:
        graph["10"] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["1", 0],
                "lora_name": lora_name,
                "strength_model": lora_strength,
            },
        }
        graph["7"]["inputs"]["model"] = ["10", 0]

    return graph


def build_zimage_workflow(
    model_key: str,
    prompt: str,
    width: int,
    height: int,
    seed: int,
    lora_name: str | None = None,
    lora_strength: float = 1.0,
    trigger_word: str = "",
    style_key: str = "none",
) -> dict[str, dict[str, Any]]:
    """Z-Image Turboの公式8ステップグラフ。

    steps 8 / cfg 1.0 / res_multistep / simple / ModelSamplingAuraFlow shift 3.0は
    Turbo蒸留の学習グリッドと一致する公式設定であり、変更すると品質が崩れる。
    ModelSamplingAuraFlowの既定shiftは3.0ではないため、必ず明示する。
    """
    definition = MODEL_DEFINITIONS[model_key]
    positive_text = compose_prompt(prompt, trigger_word, style_key)
    if not positive_text:
        raise ValueError("prompt is empty")
    # Z-Imageは辺が16の倍数である必要がある。
    width = max(16, (int(width) // 16) * 16)
    height = max(16, (int(height) // 16) * 16)

    graph: dict[str, dict[str, Any]] = {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": definition["unet"], "weight_dtype": "default"},
        },
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": ZIMAGE_TEXT_ENCODER, "type": "lumina2", "device": "default"},
        },
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": ZIMAGE_VAE}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": positive_text}},
        # Turboはcfg 1.0の蒸留モデルなのでネガティブは常にゼロ化する。
        "5": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
        "6": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1},
        },
        "7": {
            "class_type": "ModelSamplingAuraFlow",
            "inputs": {"model": ["1", 0], "shift": ZIMAGE_SHIFT},
        },
        "8": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["7", 0],
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["6", 0],
                "seed": seed,
                "steps": definition["steps"],
                "cfg": definition["cfg"],
                "sampler_name": ZIMAGE_SAMPLER,
                "scheduler": ZIMAGE_SCHEDULER,
                "denoise": 1.0,
            },
        },
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
        "10": {
            "class_type": "SaveImage",
            "inputs": {"images": ["9", 0], "filename_prefix": "ACS_ImageGen_Lite_ZImage"},
        },
    }

    if lora_name:
        graph["11"] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["1", 0],
                "lora_name": lora_name,
                "strength_model": lora_strength,
            },
        }
        graph["7"]["inputs"]["model"] = ["11", 0]

    return graph


def h3_frames(seconds: float) -> int:
    """Convert seconds to the official 24fps 17k+5 frame grid."""
    frames = max(5, round(seconds * 24))
    return frames + (5 - (frames % 17)) % 17


def build_h3_workflow(
    mode: str,
    prompt: str,
    width: int,
    height: int,
    seconds: float,
    seed: int,
    first_frame: str | None = None,
    last_frame: str | None = None,
) -> dict[str, dict[str, Any]]:
    if mode not in {"t2v", "i2v", "flf"}:
        raise ValueError("unknown H3 mode")
    if not prompt.strip():
        raise ValueError("prompt is empty")
    if mode == "i2v" and not first_frame:
        raise ValueError("first frame is required")
    if mode == "flf" and (not first_frame or not last_frame):
        raise ValueError("first and last frames are required")
    if mode == "t2v":
        first_frame = None
        last_frame = None
    elif mode == "i2v":
        last_frame = None

    graph: dict[str, dict[str, Any]] = {
        "6": {"class_type": "UNETLoader", "inputs": {
            "unet_name": "minimax_h3_fl2va_pruned_fp8_scaled.safetensors",
            "weight_dtype": "default",
        }},
        "13": {"class_type": "CLIPLoader", "inputs": {
            "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
            "type": "minimax",
            "device": "default",
        }},
        "11": {"class_type": "VAELoader", "inputs": {
            "vae_name": "minimax_h3_video_vae_fp16.safetensors",
        }},
        "24": {"class_type": "VAELoader", "inputs": {
            "vae_name": "minimax_h3_audio_vae_fp32.safetensors",
        }},
        "104": {"class_type": "MiniMaxH3ImageToVideo", "inputs": {
            "clip": ["13", 0], "vae": ["11", 0], "prompt": prompt.strip(),
            "width": width, "height": height, "length": h3_frames(seconds),
        }},
        "16": {"class_type": "BasicGuider", "inputs": {
            "model": ["6", 0], "conditioning": ["104", 0],
        }},
        "17": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
        "9": {"class_type": "BasicScheduler", "inputs": {
            "model": ["6", 0], "scheduler": "simple", "steps": 20, "denoise": 1.0,
        }},
        "15": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "14": {"class_type": "SamplerCustomAdvanced", "inputs": {
            "noise": ["15", 0], "guider": ["16", 0], "sampler": ["17", 0],
            "sigmas": ["9", 0], "latent_image": ["104", 1],
        }},
        "10": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["11", 0]}},
        "23": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["14", 0], "vae": ["24", 0]}},
        "91": {"class_type": "CreateVideo", "inputs": {
            "images": ["10", 0], "audio": ["23", 0], "fps": 24, "bit_depth": 8,
        }},
        "92": {"class_type": "SaveVideo", "inputs": {
            "video": ["91", 0], "filename_prefix": "video/ACS_Lite_H3",
            "format": "auto", "codec": "auto",
        }},
    }
    if first_frame:
        graph["121"] = {"class_type": "LoadImage", "inputs": {"image": first_frame}}
        graph["104"]["inputs"]["first_frame"] = ["121", 0]
    if last_frame:
        graph["122"] = {"class_type": "LoadImage", "inputs": {"image": last_frame}}
        graph["104"]["inputs"]["last_frame"] = ["122", 0]
    return graph
