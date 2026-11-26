import pytest

from tutor.llm.schemas import count_sentences


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", 0),
        ("   ", 0),
        ("Ein Satz ohne Punkt", 1),
        ("Ein Satz.", 1),
        ("Erster Satz. Zweiter Satz.", 2),
        ("Was ist falsch? Das Verb. Und die Form!", 3),
        ("Nach 'fui.' folgt etwas. Noch mehr.", 2),
        # Abkürzungen sind kein Satzende
        ("Das ist, z. B. bei 'ir', anders. Merke dir 'fui'.", 2),
        ("Das gilt d. h. für alle Verben. Auch für 'ser'.", 2),
        # Kleinschreibung nach dem Punkt ist kein neuer Satz
        ("Das heißt 'fui'. und nicht 'voy'.", 1),
    ],
)
def test_count_sentences(text: str, expected: int) -> None:
    assert count_sentences(text) == expected
