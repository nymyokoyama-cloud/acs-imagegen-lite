from __future__ import annotations

import json

import pytest

from app import config
from app.workflow import (
    build_h3_workflow,
    build_workflow,
    build_zimage_workflow,
    compose_prompt,
    h3_frames,
)


def test_compose_prompt_orders_trigger_prompt_and_style() -> None:
    result = compose_prompt("drinking iced coffee", "subject_token", "snapshot")
    assert result.startswith("subject_token, drinking iced coffee")
    assert "natural candid photography" in result


def test_turbo_uses_zero_negative_and_eight_steps() -> None:
    graph = build_workflow(
        "krea2_turbo", "a quiet cafe", "bad anatomy", 1024, 1024, 10
    )
    assert graph["5"]["class_type"] == "ConditioningZeroOut"
    assert graph["7"]["inputs"]["steps"] == 8
    assert graph["7"]["inputs"]["cfg"] == 1.0


def test_raw_uses_negative_and_optional_lora() -> None:
    graph = build_workflow(
        "krea2_raw",
        "a quiet cafe",
        "bad anatomy",
        1344,
        768,
        11,
        lora_name="sample.safetensors",
        lora_strength=0.8,
        trigger_word="subject_token",
    )
    assert graph["5"]["class_type"] == "CLIPTextEncode"
    assert graph["5"]["inputs"]["text"] == "bad anatomy"
    assert graph["7"]["inputs"]["model"] == ["10", 0]
    assert graph["10"]["inputs"]["lora_name"] == "sample.safetensors"


def test_empty_prompt_is_rejected() -> None:
    with pytest.raises(ValueError, match="prompt is empty"):
        build_workflow("krea2_turbo", "", "", 1024, 1024, 1)
    with pytest.raises(ValueError, match="prompt is empty"):
        build_workflow("zimage_turbo", "", "", 1024, 1024, 1)


def test_zimage_uses_the_official_distilled_settings() -> None:
    graph = build_workflow("zimage_turbo", "a quiet cafe", "bad anatomy", 1344, 768, 7)

    assert graph["1"]["inputs"]["unet_name"] == "z_image_turbo_int8_convrot.safetensors"
    assert graph["2"]["class_type"] == "CLIPLoader"
    assert graph["2"]["inputs"]["clip_name"] == config.ZIMAGE_TEXT_ENCODER
    assert graph["2"]["inputs"]["type"] == "lumina2"
    assert graph["3"]["inputs"]["vae_name"] == config.ZIMAGE_VAE
    assert graph["6"]["class_type"] == "EmptySD3LatentImage"
    assert graph["6"]["inputs"]["width"] == 1344
    assert graph["6"]["inputs"]["height"] == 768

    # ModelSamplingAuraFlowの既定は3.0ではないため、明示指定が消えていないことを守る。
    assert graph["7"]["class_type"] == "ModelSamplingAuraFlow"
    assert graph["7"]["inputs"]["shift"] == 3.0
    assert graph["7"]["inputs"]["model"] == ["1", 0]

    sampler = graph["8"]["inputs"]
    assert sampler["model"] == ["7", 0]
    assert sampler["steps"] == 8
    assert sampler["cfg"] == 1.0
    assert sampler["sampler_name"] == "res_multistep"
    assert sampler["scheduler"] == "simple"
    assert sampler["denoise"] == 1.0
    assert sampler["seed"] == 7

    # cfg 1.0の蒸留モデルなのでネガティブは常にゼロ化する。
    assert graph["5"]["class_type"] == "ConditioningZeroOut"
    assert graph["5"]["inputs"]["conditioning"] == ["4", 0]
    assert "bad anatomy" not in json.dumps(graph, ensure_ascii=False)

    assert graph["9"]["class_type"] == "VAEDecode"
    assert graph["10"]["class_type"] == "SaveImage"
    assert "11" not in graph


def test_zimage_applies_lora_before_model_sampling() -> None:
    graph = build_zimage_workflow(
        "zimage_turbo",
        "a quiet cafe",
        1024,
        1024,
        12,
        lora_name="brought.safetensors",
        lora_strength=0.7,
        trigger_word="subject_token",
        style_key="snapshot",
    )
    assert graph["11"]["class_type"] == "LoraLoaderModelOnly"
    assert graph["11"]["inputs"]["model"] == ["1", 0]
    assert graph["11"]["inputs"]["lora_name"] == "brought.safetensors"
    assert graph["11"]["inputs"]["strength_model"] == 0.7
    assert graph["7"]["inputs"]["model"] == ["11", 0]
    assert graph["4"]["inputs"]["text"].startswith("subject_token, a quiet cafe")
    assert "natural candid photography" in graph["4"]["inputs"]["text"]


def test_zimage_rounds_sides_down_to_a_multiple_of_sixteen() -> None:
    graph = build_zimage_workflow("zimage_turbo", "a quiet cafe", 1030, 777, 1)
    assert graph["6"]["inputs"]["width"] == 1024
    assert graph["6"]["inputs"]["height"] == 768


def test_every_supported_ratio_is_a_multiple_of_sixteen_for_zimage() -> None:
    for width, height in config.SIZES.values():
        graph = build_workflow("zimage_turbo", "a quiet cafe", "", width, height, 1)
        assert graph["6"]["inputs"]["width"] == width
        assert graph["6"]["inputs"]["height"] == height


def test_h3_frame_grid_matches_24fps_17k_plus_5() -> None:
    assert h3_frames(5) == 124
    assert h3_frames(10) == 243


def test_h3_supports_text_image_and_first_last_modes() -> None:
    text_graph = build_h3_workflow("t2v", "a calm ocean", 864, 480, 5, 1)
    assert text_graph["104"]["class_type"] == "MiniMaxH3ImageToVideo"
    assert "first_frame" not in text_graph["104"]["inputs"]
    assert text_graph["17"]["inputs"]["sampler_name"] == "res_multistep"
    assert text_graph["9"]["inputs"]["steps"] == 20
    assert text_graph["91"]["inputs"]["fps"] == 24

    image_graph = build_h3_workflow(
        "i2v", "the person smiles", 480, 864, 5, 2, first_frame="first.png"
    )
    assert image_graph["104"]["inputs"]["first_frame"] == ["121", 0]
    assert "last_frame" not in image_graph["104"]["inputs"]

    frame_graph = build_h3_workflow(
        "flf", "walk from the first scene to the last", 672, 672, 5, 3,
        first_frame="first.png", last_frame="last.webp",
    )
    assert frame_graph["104"]["inputs"]["first_frame"] == ["121", 0]
    assert frame_graph["104"]["inputs"]["last_frame"] == ["122", 0]


def test_h3_required_frames_are_enforced() -> None:
    with pytest.raises(ValueError, match="first frame"):
        build_h3_workflow("i2v", "move", 864, 480, 5, 1)
    with pytest.raises(ValueError, match="first and last"):
        build_h3_workflow("flf", "move", 864, 480, 5, 1, first_frame="a.png")
