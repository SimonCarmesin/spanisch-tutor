"""Grundbegriffe der Fachdomäne, unabhängig von Datenbank und API."""

from enum import StrEnum


class CefrLevel(StrEnum):
    """Sprachniveau nach dem Gemeinsamen Europäischen Referenzrahmen."""

    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class Role(StrEnum):
    """Absender einer Nachricht im Gespräch."""

    USER = "user"
    ASSISTANT = "assistant"


class ErrorCategory(StrEnum):
    """Fehlerkategorien. Die Werte dienen als stabile Schlüssel für Statistiken."""

    PRESENTE = "presente"
    PRETERITO_INDEFINIDO = "preterito_indefinido"
    PRETERITO_IMPERFECTO = "preterito_imperfecto"
    PRETERITO_PERFECTO = "preterito_perfecto"
    FUTURO = "futuro"
    CONDICIONAL = "condicional"
    SUBJUNTIVO = "subjuntivo"
    IMPERATIVO = "imperativo"
    SER_ESTAR = "ser_estar"
    ARTICULOS_GENERO = "articulos_genero"
    CONCORDANCIA = "concordancia"
    PREPOSICIONES = "preposiciones"
    PRONOMBRES = "pronombres"
    ORDEN_PALABRAS = "orden_palabras"
    VOCABULARIO = "vocabulario"
    ORTOGRAFIA = "ortografia"
    OTRO = "otro"
