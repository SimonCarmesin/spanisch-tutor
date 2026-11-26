import { useMemo, useState } from "react";
import { createApi, type StartSessionResponse } from "./api/client";
import { BottomNav, type Tab } from "./components/BottomNav";
import type { ConversationState } from "./conversation/state";
import { clearSavedConversation, loadSavedConversation } from "./conversation/useConversation";
import { ConversationScreen } from "./screens/ConversationScreen";
import { MapScreen } from "./screens/MapScreen";
import { PlaceholderScreen } from "./screens/PlaceholderScreen";
import { SettingsScreen } from "./screens/SettingsScreen";
import { useToken } from "./settings";

type Conversation = StartSessionResponse | ConversationState;

function sessionIdOf(c: Conversation): string {
  return "session_id" in c ? c.session_id : c.session.id;
}

export function App() {
  const [token, setToken] = useToken();
  const api = useMemo(() => createApi({ token }), [token]);
  const [tab, setTab] = useState<Tab>("karte");
  // Ein laufendes Gespräch überlebt Neuladen und App-Wechsel (gespeichert im Gerät)
  const [conversation, setConversation] = useState<Conversation | null>(() => loadSavedConversation());
  const [inConversation, setInConversation] = useState(() => conversation !== null);

  const startConversation = async (scenarioId: string) => {
    const started = await api.startSession(scenarioId);
    clearSavedConversation();
    setConversation(started);
    setInConversation(true);
  };

  const leaveConversation = () => {
    // Den gespeicherten, aktuellen Stand übernehmen, damit "Fortsetzen" alles wiederherstellt
    setConversation(loadSavedConversation());
    setInConversation(false);
  };

  const finishConversation = () => {
    clearSavedConversation();
    setConversation(null);
    setInConversation(false);
  };

  let content;
  if (tab === "karte" && inConversation && conversation) {
    content = (
      <ConversationScreen
        key={sessionIdOf(conversation)}
        api={api}
        start={conversation}
        onLeave={leaveConversation}
        onFinished={finishConversation}
      />
    );
  } else if (tab === "karte") {
    content = (
      <MapScreen
        api={api}
        hasToken={token !== ""}
        hasOpenConversation={conversation !== null}
        onResume={() => setInConversation(true)}
        onStart={startConversation}
        onOpenSettings={() => setTab("einstellungen")}
      />
    );
  } else if (tab === "trainer") {
    content = (
      <PlaceholderScreen
        title="Trainer"
        text="Hier kommt als Nächstes der Satztrainer: ganze Sätze von Deutsch nach Spanisch und zurück, mit Hilfestufen und deinen eigenen Fehlern als Übungsmaterial."
      />
    );
  } else if (tab === "fehler") {
    content = (
      <PlaceholderScreen
        title="Fehler"
        text="Hier siehst du bald alle deine Fehler nach Kategorie, wie weit du sie schon beherrschst, und kannst gezielt mit ihnen üben."
      />
    );
  } else {
    content = <SettingsScreen api={api} token={token} onTokenChange={setToken} />;
  }

  return (
    <div className="app">
      <main>{content}</main>
      <BottomNav active={tab} onChange={setTab} />
    </div>
  );
}
