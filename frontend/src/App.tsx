import { Navigate, Route, Routes, useParams } from "react-router-dom";

import { ConfirmationPage } from "./pages/ConfirmationPage";
import { CreateMatchPage } from "./pages/CreateMatchPage";
import { EntryPage } from "./pages/EntryPage";
import { JoinMatchPage } from "./pages/JoinMatchPage";
import { LobbyPage } from "./pages/LobbyPage";
import { PartnerAQuestionnairePage } from "./pages/PartnerAQuestionnairePage";
import { PlayEntryPage } from "./pages/PlayEntryPage";
import { PlayerASetupPage } from "./pages/PlayerASetupPage";
import { PlayerBSetupPage } from "./pages/PlayerBSetupPage";
import { PlayPage } from "./pages/PlayPage";

function AvatarRedirect() {
  const { gameId } = useParams<{ gameId: string }>();
  return <Navigate to={`/games/${gameId}/player-a`} replace />;
}

export function App() {
  return (
    <Routes>
      <Route path="/" element={<EntryPage />} />
      <Route path="/lobby" element={<LobbyPage />} />
      <Route path="/games/new" element={<CreateMatchPage />} />
      <Route path="/games/join" element={<JoinMatchPage />} />
      <Route path="/games/join/:matchName" element={<JoinMatchPage />} />
      <Route path="/games/:gameId/player-a" element={<PlayerASetupPage />} />
      <Route path="/games/:gameId/player-b" element={<PlayerBSetupPage />} />
      <Route path="/games/:gameId/confirm" element={<ConfirmationPage />} />
      <Route
        path="/games/:gameId/partner-a/questions"
        element={<PartnerAQuestionnairePage />}
      />
      <Route path="/games/:gameId/play" element={<PlayEntryPage />} />
      <Route path="/games/:gameId/play/:runId" element={<PlayPage />} />
      <Route path="/create" element={<Navigate to="/games/new" replace />} />
      <Route path="/games/:gameId/avatar" element={<AvatarRedirect />} />
      <Route path="*" element={<Navigate to="/lobby" replace />} />
    </Routes>
  );
}
