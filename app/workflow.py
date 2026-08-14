from __future__ import annotations

from typing import Any

from .config import MODEL_DEFINITIONS, STYLES, TEXT_ENCODER, VAE


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
