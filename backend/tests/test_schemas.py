import pytest
from pydantic import ValidationError

from tests.conftest import make_correction
from tutor.domain import ErrorCategory
from tutor.llm.schemas import Correction, TutorTurn


def test_valid_correction_is_accepted() -> None:
    correction = make_correction()
    assert correction.category is ErrorCategory.PRETERITO_INDEFINIDO


def test_explanation_with_three_sentences_is_rejected() -> None:
    with pytest.raises(ValidationError, match="höchstens 2 Sätze"):
        make_correction(explanation="Eins ist falsch. Zwei ist auch falsch. Drei gibt es nicht.")


def test_overlong_explanation_is_rejected() -> None:
    with pytest.raises(ValidationError, match="Zeichen"):
        make_correction(explanation="Das ist falsch " + "und noch viel mehr " * 30 + ".")


def test_identical_original_and_correction_is_rejected() -> None:
    with pytest.raises(ValidationError, match="identisch"):
        make_correction(original="Ayer fui.", corrected="Ayer fui.")


@pytest.mark.parametrize("field", ["original", "corrected", "explanation"])
def test_blank_fields_are_rejected(field: str) -> None:
    values = {
        "original": "voy",
        "corrected": "fui",
        "category": ErrorCategory.OTRO,
        "explanation": "Falsche Zeitform.",
    }
    values[field] = "   "
    with pytest.raises(ValidationError):
        Correction(**values)


def test_unknown_category_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Correction.model_validate(
            {"original": "a", "corrected": "b", "category": "erfunden", "explanation": "Falsch."}
        )


def test_too_many_corrections_are_rejected() -> None:
    corrections = [make_correction(original=f"fehler {i}") for i in range(4)]
    with pytest.raises(ValidationError, match="Höchstens 3"):
        TutorTurn(reply="Hola", corrections=corrections)


def test_blank_reply_is_rejected() -> None:
    with pytest.raises(ValidationError):
        TutorTurn(reply="  ", corrections=[])
