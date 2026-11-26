import type { Correction } from "../api/client";

/** Lesbare Namen der Fehlerkategorien (die Schlüssel kommen stabil aus dem Backend). */
export const CATEGORY_LABELS: Record<Correction["category"], string> = {
  presente: "Presente",
  preterito_indefinido: "Pretérito indefinido",
  preterito_imperfecto: "Pretérito imperfecto",
  preterito_perfecto: "Pretérito perfecto",
  futuro: "Futuro",
  condicional: "Condicional",
  subjuntivo: "Subjuntivo",
  imperativo: "Imperativo",
  ser_estar: "Ser vs. estar",
  articulos_genero: "Artikel und Genus",
  concordancia: "Angleichung",
  preposiciones: "Präpositionen",
  pronombres: "Pronomen",
  orden_palabras: "Wortstellung",
  vocabulario: "Wortschatz",
  ortografia: "Rechtschreibung",
  otro: "Sonstiges",
};

export function CorrectionCard({ correction }: { correction: Correction }) {
  return (
    <article className="correction-card">
      <span className="chip">{CATEGORY_LABELS[correction.category]}</span>
      <p className="correction-original">
        <del>{correction.original}</del>
      </p>
      <p className="correction-fixed">{correction.corrected}</p>
      <p className="correction-explanation">{correction.explanation}</p>
    </article>
  );
}
