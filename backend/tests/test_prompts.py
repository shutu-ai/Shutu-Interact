"""Prompt template content rules (age layering, safety, topic lock)."""

from app.providers.prompts import build_system_prompt


def test_prompt_contains_role_topic_and_dialogue_rules():
    prompt = build_system_prompt("7-9", "animals", 4)

    assert "Coco" in prompt
    assert "animals" in prompt
    assert "one question" in prompt.lower()
    assert "English" in prompt


def test_prompt_identity_is_a_robot_not_an_animal_mascot():
    """B-10 (MVP closure): the mascot art is a blue-and-orange robot; the
    prompt must not call Coco a camel (or any other animal species)."""
    prompt = build_system_prompt("7-9", "animals", 4).lower()

    assert "robot" in prompt
    assert "camel" not in prompt


def test_prompt_varies_by_age_group():
    prompts = {
        group: build_system_prompt(group, "sports", 4)
        for group in ("4-6", "7-9", "10-12")
    }

    assert len(set(prompts.values())) == 3
    assert "4-6" in prompts["4-6"] or "4 to 6" in prompts["4-6"]
    assert "7-9" in prompts["7-9"] or "7 to 9" in prompts["7-9"]
    assert "10-12" in prompts["10-12"] or "10 to 12" in prompts["10-12"]


def test_prompt_contains_safety_rules():
    prompt = build_system_prompt("4-6", "colors", 4).lower()

    assert "personal information" in prompt
    assert "violence" in prompt
    assert "guardian" in prompt
    assert "medical" in prompt
