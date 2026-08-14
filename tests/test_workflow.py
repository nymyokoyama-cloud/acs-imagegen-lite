from __future__ import annotations

import pytest

from app.workflow import build_h3_workflow, build_workflow, compose_prompt, h3_frames


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
