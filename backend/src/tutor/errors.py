"""Fachliche Fehler. Die Zuordnung zu HTTP-Status passiert in der API-Schicht."""


class TutorError(Exception):
    """Basis aller fachlichen Fehler."""

    code = "tutor_error"


class UnknownScenarioError(TutorError):
    code = "unknown_scenario"


class SessionNotFoundError(TutorError):
    code = "session_not_found"


class SessionClosedError(TutorError):
    code = "session_closed"


class TurnLimitReachedError(TutorError):
    code = "turn_limit_reached"


class ConcurrentTurnError(TutorError):
    code = "concurrent_turn"


class LLMError(TutorError):
    """Basis der Fehler beim Aufruf des Sprachmodells."""

    code = "llm_error"


class LLMUnavailableError(LLMError):
    code = "llm_unavailable"


class LLMRateLimitError(LLMError):
    code = "llm_rate_limited"


class LLMOutputError(LLMError):
    """Das Modell lieferte auch nach einem Wiederholungsversuch keine gültige Ausgabe."""

    code = "llm_invalid_output"
