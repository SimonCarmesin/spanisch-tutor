"""Ausgabeformat des Sprachmodells und dessen Prüfregeln.

Die Prüfregeln (zum Beispiel höchstens zwei Sätze pro Erklärung) stehen bewusst nicht im
JSON-Schema, das an das Modell geht, sondern in Validatoren. Verletzt das Modell eine Regel,
löst das den Wiederholungsversuch im Client aus.
"""

import re

from pydantic import BaseModel, Field, field_validator, model_validator

from tutor.domain import ErrorCategory

MAX_EXPLANATION_SENTENCES = 2
MAX_EXPLANATION_CHARS = 320
MAX_CORRECTIONS_PER_TURN = 3

# Abkürzungen, deren Punkt kein Satzende ist
_ABBREVIATIONS = re.compile(r"\b(z\. ?B|d\. ?h|u\. ?a|bzw|usw|ca|Nr|etc|ggf|vgl)\.", re.IGNORECASE)
# Satzende: Satzzeichen, optional schließende Anführungszeichen, dann Leerraum und ein Satzanfang
_SENTENCE_BOUNDARY = re.compile(r"""(?<=[.!?…])["'“”»«)]*\s+(?=[A-ZÄÖÜÁÉÍÓÚÑ¡¿"'„»«“(0-9])""")


def count_sentences(text: str) -> int:
    """Zählt Sätze grob, aber stabil genug für die Längenregel der Erklärungen."""
    cleaned = _ABBREVIATIONS.sub(lambda m: m.group(0).replace(".", ""), text.strip())
    if not cleaned:
        return 0
    return len(_SENTENCE_BOUNDARY.split(cleaned))


class Correction(BaseModel):
    original: str = Field(
        description="Die fehlerhafte Stelle oder der fehlerhafte Satz des Lernenden"
    )
    corrected: str = Field(description="Die korrigierte Fassung")
    category: ErrorCategory = Field(description="Fehlerkategorie aus der vorgegebenen Liste")
    explanation: str = Field(
        description=(
            "Auf Deutsch, höchstens zwei Sätze: was falsch war, warum, und wie es richtig heißt"
        )
    )

    @field_validator("original", "corrected", "explanation")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("darf nicht leer sein")
        return value

    @field_validator("explanation")
    @classmethod
    def _explanation_is_short(cls, value: str) -> str:
        if count_sentences(value) > MAX_EXPLANATION_SENTENCES:
            raise ValueError(
                f"Die Erklärung darf höchstens {MAX_EXPLANATION_SENTENCES} Sätze haben"
            )
        if len(value) > MAX_EXPLANATION_CHARS:
            raise ValueError(f"Die Erklärung darf höchstens {MAX_EXPLANATION_CHARS} Zeichen haben")
        return value

    @model_validator(mode="after")
    def _actually_a_correction(self) -> "Correction":
        if self.original.strip() == self.corrected.strip():
            raise ValueError("Original und Korrektur sind identisch")
        return self


class TutorTurn(BaseModel):
    reply: str = Field(description="Antwort des Gesprächspartners auf Spanisch, in der Rolle")
    corrections: list[Correction] = Field(
        description="Korrekturen zur letzten Nachricht des Lernenden, leer wenn fehlerfrei"
    )

    @field_validator("reply")
    @classmethod
    def _reply_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Die Antwort darf nicht leer sein")
        return value

    @field_validator("corrections")
    @classmethod
    def _not_too_many(cls, value: list[Correction]) -> list[Correction]:
        if len(value) > MAX_CORRECTIONS_PER_TURN:
            raise ValueError(f"Höchstens {MAX_CORRECTIONS_PER_TURN} Korrekturen pro Beitrag")
        return value
