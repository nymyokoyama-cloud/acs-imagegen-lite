from __future__ import annotations

import pytest

from app.workflow import build_workflow, compose_prompt


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

