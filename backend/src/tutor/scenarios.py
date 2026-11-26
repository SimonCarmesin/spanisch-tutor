"""Katalog der Gesprächsszenarien."""

from dataclasses import dataclass
from typing import Final

from tutor.errors import UnknownScenarioError


@dataclass(frozen=True, slots=True)
class Scenario:
    id: str
    title: str
    partner_role: str
    learner_goal: str
    # Themengrenze für den Systemprompt (FR-4, NFR-2)
    topic_boundary: str = "Bleibe beim Szenario und lenke freundlich dorthin zurück."


FREE_SCENARIO_ID: Final = "frei"


_SCENARIOS: Final[tuple[Scenario, ...]] = (
    Scenario(
        id=FREE_SCENARIO_ID,
        title="Freies Gespräch",
        partner_role=(
            "Lucía, eine freundliche, neugierige Spanierin aus Madrid, die sich gern unterhält"
        ),
        learner_goal=(
            "Über ein Thema seiner Wahl sprechen. Nennt er keins, schlage ein Alltagsthema vor"
        ),
        topic_boundary=(
            "Das Thema ist frei, aber du bist nur Gesprächspartnerin für eine Sprachübung. "
            "Lehne Aufgaben ab, die keine Unterhaltung sind (zum Beispiel Programmcode, "
            "Hausaufgaben, lange Texte), und schlage vor, stattdessen darüber zu sprechen."
        ),
    ),
    Scenario(
        id="cafe",
        title="Im Café bestellen",
        partner_role="Kellner oder Kellnerin in einem Café in Madrid",
        learner_goal="Getränke und etwas zu essen bestellen und nach der Rechnung fragen",
    ),
    Scenario(
        id="arzt",
        title="Beim Arzt",
        partner_role="Mitarbeiter an der Anmeldung einer Arztpraxis in Valencia",
        learner_goal="Einen Termin vereinbaren und kurz beschreiben, was einem fehlt",
    ),
    Scenario(
        id="wohnung",
        title="Wohnungssuche",
        partner_role="Vermieter einer Wohnung in Barcelona, der am Telefon Fragen beantwortet",
        learner_goal="Nach Miete, Lage, Ausstattung und Besichtigungstermin fragen",
    ),
    Scenario(
        id="restaurant",
        title="Im Restaurant",
        partner_role="Kellner in einem Restaurant in Sevilla",
        learner_goal="Einen Tisch reservieren, bestellen und besondere Wünsche nennen",
    ),
    Scenario(
        id="einkaufen",
        title="Einkaufen",
        partner_role="Verkäuferin in einem Bekleidungsgeschäft in Málaga",
        learner_goal="Nach Größen, Farben und Preisen fragen und etwas anprobieren",
    ),
)

SCENARIOS: Final[dict[str, Scenario]] = {s.id: s for s in _SCENARIOS}


def get_scenario(scenario_id: str) -> Scenario:
    try:
        return SCENARIOS[scenario_id]
    except KeyError:
        raise UnknownScenarioError(f"Unbekanntes Szenario: {scenario_id}") from None
