import type { ReactNode } from "react";
import { ErrorsIcon, MapIcon, SettingsIcon, TrainerIcon } from "./Icons";

export type Tab = "karte" | "trainer" | "fehler" | "einstellungen";

const TABS: { id: Tab; label: string; icon: ReactNode }[] = [
  { id: "karte", label: "Karte", icon: <MapIcon /> },
  { id: "trainer", label: "Trainer", icon: <TrainerIcon /> },
  { id: "fehler", label: "Fehler", icon: <ErrorsIcon /> },
  { id: "einstellungen", label: "Einstellungen", icon: <SettingsIcon /> },
];

export function BottomNav({ active, onChange }: { active: Tab; onChange: (tab: Tab) => void }) {
  return (
    <nav className="bottom-nav" aria-label="Hauptnavigation">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          type="button"
          className={tab.id === active ? "active" : ""}
          aria-current={tab.id === active ? "page" : undefined}
          onClick={() => onChange(tab.id)}
        >
          {tab.icon}
          <span>{tab.label}</span>
        </button>
      ))}
    </nav>
  );
}
