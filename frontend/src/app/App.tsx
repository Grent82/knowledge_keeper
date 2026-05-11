import { BrowserRouter, Route, Routes } from "react-router-dom";

import { AppScreen } from "../features/app-shell/AppScreen";
import { AppShell } from "./AppShell";

export function App() {
  const screen = (
    <AppShell>
      <AppScreen />
    </AppShell>
  );

  return (
    <BrowserRouter>
      <Routes>
        <Route element={screen} path="/" />
        <Route element={screen} path="/c/:categoryId" />
        <Route element={screen} path="/m/:mediaItemId" />
        <Route element={screen} path="/c/:categoryId/m/:mediaItemId" />
      </Routes>
    </BrowserRouter>
  );
}
