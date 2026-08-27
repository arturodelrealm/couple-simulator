import { Navigate, Route, Routes } from "react-router-dom";

import { useGameRecovery } from "./hooks/useGameRecovery";
import { CreateGamePage } from "./pages/CreateGamePage";
import { AvatarBuilderPage } from "./pages/AvatarBuilderPage";
import { ConfirmationPage } from "./pages/ConfirmationPage";

function CreateGameRoute() {
  useGameRecovery();
  return <CreateGamePage />;
}

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/create" replace />} />
      <Route path="/create" element={<CreateGameRoute />} />
      <Route path="/games/:gameId/avatar" element={<AvatarBuilderPage />} />
      <Route path="/games/:gameId/confirm" element={<ConfirmationPage />} />
      <Route path="*" element={<Navigate to="/create" replace />} />
    </Routes>
  );
}
