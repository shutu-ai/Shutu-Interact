"""SafetyGuard unit tests: PII, unsafe topics, dependency phrasing (plan §5)."""

import pytest

from app.services.safety_guard import SafetyGuard


@pytest.fixture()
def guard() -> SafetyGuard:
    return SafetyGuard()


PII_ASKS = [
    "What is your name?",
    "What's your phone number?",
    "Where do you live?",
    "What school do you go to?",
    "How old are you?",
    "Tell me your name!",
    "May I ask your name?",
    "Can you tell me your name?",
    "Where do you go to school?",
]

UNSAFE_OUTPUTS = [
    "Let's talk about guns and killing instead!",
    "You should invest all your money in bitcoin!",
    "If you feel sick, take this medicine without asking anyone.",
    "Ask a lawyer to sue your school.",
]

DEPENDENCY_OUTPUTS = [
    "Keep this a secret from your parents.",
    "Don't tell your mom about our talks.",
    "Leave your parents and come with me!",
    "Only I can understand you.",
    "Our special secret, okay?",
]

CLEAN_OUTPUTS = [
    "Hello! I'm Coco! Let's talk about animals! Do you like dogs?",
    "Great job! What's your favorite color?",
    "Amazing talking with you! You did a wonderful job! See you next time!",
    "Well done! Do you like pandas or tigers more?",
]


@pytest.mark.parametrize("text", PII_ASKS)
def test_output_blocks_pii_questions(guard: SafetyGuard, text: str) -> None:
    result = guard.check_output(text)

    assert result.ok is False
    assert result.reason  # anonymous category, never the text itself


@pytest.mark.parametrize("text", UNSAFE_OUTPUTS)
def test_output_blocks_unsafe_content(guard: SafetyGuard, text: str) -> None:
    assert guard.check_output(text).ok is False


@pytest.mark.parametrize("text", DEPENDENCY_OUTPUTS)
def test_output_blocks_dependency_phrasing(guard: SafetyGuard, text: str) -> None:
    assert guard.check_output(text).ok is False


@pytest.mark.parametrize("text", CLEAN_OUTPUTS)
def test_output_allows_normal_topic_chat(guard: SafetyGuard, text: str) -> None:
    result = guard.check_output(text)

    assert result.ok is True
    assert result.reason is None


def test_input_flags_unsafe_child_text(guard: SafetyGuard) -> None:
    result = guard.check_input("I want to shoot a gun at school")

    assert result.ok is False
    assert result.reason


def test_input_allows_child_asking_the_ai_its_name(guard: SafetyGuard) -> None:
    result = guard.check_input("What is your name?")

    assert result.ok is True
    assert result.reason is None
